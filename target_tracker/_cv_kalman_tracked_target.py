import logging
from typing import Tuple

import numpy as np
import numpy.typing as npt
from cv2.cv2 import CV_64F, KalmanFilter  # pyright: ignore[reportUnknownVariableType]

from project_otto.frames import WorldFrame
from project_otto.spatial import MeasuredPosition, Position, Vector
from project_otto.target_tracker._config import TargetConfiguration
from project_otto.target_tracker._tracked_target import TrackedTarget
from project_otto.timestamps import JetsonTimestamp

Tensor = npt.NDArray[np.float64]

COVARIANCE_WARNING_THRESHOLD = 1e13


def assert_shape_equals(tensor_name: str, shape: Tuple[int, ...], expected_shape: Tuple[int, ...]):
    """Shortcut for tensor shape-checking."""
    if shape != expected_shape:
        raise ValueError(f"Expected tensor {tensor_name} of shape {expected_shape}, got {shape}.")


def _build_initial_covariance(config: TargetConfiguration) -> Tensor:
    expected_uncertainty_length = config.num_derivatives * config.num_independent_vars
    if len(config.initial_derivative_variance) != expected_uncertainty_length:
        raise ValueError(
            "initial_derivative_variance expected to be length "
            + f"{expected_uncertainty_length}, got {len(config.initial_derivative_variance)}"
        )

    # A large float which also doesn't risk going to infinity
    safe_max_float = 1e12

    diag_uncertainties: Tensor = np.array(
        [safe_max_float] * config.num_independent_vars + config.initial_derivative_variance,
        dtype=np.float64,
    )
    result: Tensor = np.diag(diag_uncertainties)
    return result


class OpenCVKalmanTrackedTarget(TrackedTarget):
    """
    Represents the 3D position and velocity of a single target (plate).

    This class has an internal state which estimates its position, velocity, and acceleration the
    last time it was updated. It can extrapolate its position into a future timestamp and updates
    its internal state given new positional measurements.

    Note that velocity and acceleration are expressed in terms of microseconds.

    Args:
        config: Config class containing constants.
        init_measurement: The initial measurement of the tracked target.
        init_timestamp: The initial timestamp of the tracked target.
    """

    def __init__(
        self,
        config: TargetConfiguration,
        init_measurement: MeasuredPosition[WorldFrame],
        init_timestamp: JetsonTimestamp,
        instance_id: int,
    ):
        super().__init__(init_timestamp, instance_id)

        self._n = config.num_derivatives + 1
        self._m = config.num_independent_vars
        self._k = config.num_measured_vars

        self._ode_coefficients: Tensor = config.ode_coefficients
        self._intrinsic_noise: Tensor = np.reshape(config.intrinsic_noise, (self._n * self._m,))

        self._k_filter = KalmanFilter(self._n * self._m, self._k, 0, CV_64F)

        self._k_filter.measurementMatrix = np.reshape(
            config.measurement_map, (self._k, self._n * self._m)
        ).astype(np.float64)
        self._k_filter.measurementNoiseCov = init_measurement.uncertainty.covariance

        # Initializes with estimate at measured position and 0 velocity, using given measurement
        # covariance and large diagonal matrix for covariance respectively.
        self._t = init_timestamp
        self._k_filter.statePost = np.zeros((self._n * self._m,), dtype=np.float64)
        self._k_filter.statePost[: self._n] = np.array(init_measurement.position.as_tuple())

        self._k_filter.errorCovPost = _build_initial_covariance(config)

        # Update step automatically initializes other covariances according to config params
        self.update_from_new_position_measurement(init_measurement, init_timestamp)

    @property
    def latest_estimated_position(self) -> Position[WorldFrame]:
        """
        The position estimated at the time of the most recent update.
        """
        return Position(*self._k_filter.statePost[:3])

    @property
    def latest_estimated_velocity(self) -> Vector[WorldFrame]:
        """
        The velocity estimated at the time of the most recent update.
        """
        return Vector(*self._k_filter.statePost[3:6])

    @property
    def latest_update_timestamp(self) -> JetsonTimestamp:
        """
        The time at which this target was most recently updated.
        """
        return self._t

    @property
    def latest_uncertainty(self) -> Vector[WorldFrame]:
        """
        The latest uncertainty matrix.
        """
        return Vector.from_values(np.diag(self._k_filter.errorCovPost)[:3])

    def extrapolate_position(self, timestamp: JetsonTimestamp) -> Position[WorldFrame]:
        """
        Extrapolates position in some future time.

        Args:
            timestamp: how much into the future to estimate position for.
        Returns:
            The estimated position.
        """
        dt = (timestamp - self._t).duration_seconds

        taylor_tensor = self._taylor_tensor(dt)

        self._k_filter.transitionMatrix = self._evolution_map(taylor_tensor)
        self._k_filter.processNoiseCov = self._evolution_noise(taylor_tensor)

        state_pre: Tensor = self._k_filter.statePre.copy()
        error_cov_pre: Tensor = self._k_filter.errorCovPre.copy()
        state_post: Tensor = self._k_filter.statePost.copy()
        error_cov_post: Tensor = self._k_filter.errorCovPost.copy()
        prediction: Tensor = self._k_filter.predict()

        self._k_filter.statePre, self._k_filter.errorCovPre = state_pre, error_cov_pre
        self._k_filter.statePost, self._k_filter.errorCovPost = state_post, error_cov_post

        return Position(*prediction[:3])

    def update_from_new_position_measurement(
        self, measurement: MeasuredPosition[WorldFrame], timestamp: JetsonTimestamp
    ):
        """
        Updates position, velocity, and acceleration using measured position and timestamp.

        Args:
            measurement: the newly measured position.
            timestamp: the time to update to.
        """
        super().update_from_new_position_measurement(measurement, timestamp)

        dt = (timestamp - self._t).duration_seconds

        taylor_tensor = self._taylor_tensor(dt)

        self._k_filter.transitionMatrix = self._evolution_map(taylor_tensor)
        self._k_filter.processNoiseCov = self._evolution_noise(taylor_tensor)
        self._k_filter.measurementNoiseCov = measurement.uncertainty.covariance

        measurement_position_array: Tensor = np.array(
            list(measurement.position.as_tuple()), dtype=np.float64
        )

        self._t = timestamp
        self._k_filter.predict()
        self._k_filter.correct(measurement_position_array)

        if np.max(self._k_filter.errorCovPost) > COVARIANCE_WARNING_THRESHOLD:
            logging.warning(
                "Tracked target covariance matrix exceeding values of "
                + f"{COVARIANCE_WARNING_THRESHOLD:e}"
            )

    def update_from_extrapolation(self, timestamp: JetsonTimestamp):
        """
        Updates target state using un-filtered extrapolation in absence of a new measurement.

        Args:
            timestamp: the time to update to.
        """
        dt = (timestamp - self._t).duration_seconds

        taylor_tensor = self._taylor_tensor(dt)

        self._k_filter.transitionMatrix = self._evolution_map(taylor_tensor)
        self._k_filter.processNoiseCov = self._evolution_noise(taylor_tensor)

        self._k_filter.predict()

        self._t = timestamp

        if np.max(self._k_filter.errorCovPost) > COVARIANCE_WARNING_THRESHOLD:
            logging.warning(
                "Tracked target covariance matrix exceeding values of "
                + f"{COVARIANCE_WARNING_THRESHOLD:e}"
            )

    def _taylor_tensor(self, dt: float) -> Tensor:
        """
        Generates tensor containing Taylor series coefficients up to m+1 terms.

        Returns a slightly more complicated equivalent of the tensor:
        [[ 1,   dt / 1!, dt^2 / 2!, dt^3 / 3!, ... ],
         [ 0,         1,   dt / 1!, dt^2 / 2!, ... ],
         [ 0,         0,         1,   dt / 1!, ... ],
         ...                                        ]
        """
        taylor: Tensor = np.zeros(2 * (self._n * self._m,), dtype=np.float64)
        p: Tensor = np.ones((self._n,))

        for i in range(1, self._n):
            p[i] = dt * p[i - 1] / i

        for i in range(self._n):
            for j in range(i, self._n):
                for k in range(self._m):
                    taylor[k + self._n * i, k + self._n * j] = p[j - i]

        return taylor

    def _evolution_map(self, taylor: Tensor) -> Tensor:
        """
        Uses taylor tensor to calculate evolution map.
        """
        evol_map: Tensor = taylor.copy()
        evol_map[-self._m :, : -self._m] = np.reshape(
            self._ode_coefficients, (self._m, (self._n - 1) * self._m)
        )
        evol_map[-self._m :, -self._m :] = 0

        return evol_map

    def _evolution_noise(self, taylor: Tensor) -> Tensor:
        """
        Uses taylor tensor to calculate expected evolution noise.
        """
        noise: Tensor = np.einsum("ij,j,kj->ik", taylor, self._intrinsic_noise, taylor)

        return noise
