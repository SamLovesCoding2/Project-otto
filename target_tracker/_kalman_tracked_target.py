import logging
from typing import Tuple

import numpy as np
import numpy.typing as npt

from project_otto.frames import WorldFrame
from project_otto.spatial import MeasuredPosition, Position, Vector
from project_otto.target_tracker._config import TargetConfiguration
from project_otto.target_tracker._tracked_target import TrackedTarget
from project_otto.target_tracker.estimators import Estimation, KalmanFilter
from project_otto.timestamps import JetsonTimestamp

Tensor = npt.NDArray[np.float64]

COVARIANCE_WARNING_THRESHOLD = 1e13


def assert_shape_equals(tensor_name: str, shape: Tuple[int, ...], expected_shape: Tuple[int, ...]):
    """Shortcut for tensor shape-checking."""
    if shape != expected_shape:
        raise ValueError(f"Expected tensor {tensor_name} of shape {expected_shape}, got {shape}.")


class KalmanTrackedTarget(TrackedTarget):
    """
    Represents the 3D position and velocity of a single target (plate).

    This class has an internal state which estimates its position, velocity, and acceleration the
    last time it was updated. It can extrapolate its position into a future timestamp and updates
    its internal state given new positional measurements.

    Note that velocity and acceleration are expressed in terms of microseconds.

    Args:
        config: Config class containing constants.
        init_position: The initial position of the tracked target.
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

        n = (config.num_derivatives + 1, config.num_independent_vars)
        k = (config.num_measured_vars,)

        self._ode_coefficients: Tensor = config.ode_coefficients
        self._intrinsic_noise: Tensor = config.intrinsic_noise

        self._k_filter = KalmanFilter(
            n,
            k,
            config.measurement_map,
        )

        expected_uncertainty_length = config.num_derivatives * config.num_independent_vars
        if len(config.initial_derivative_variance) != expected_uncertainty_length:
            raise ValueError(
                "initial_derivative_variance expected to be length "
                + f"{expected_uncertainty_length}, got {len(config.initial_derivative_variance)}"
            )

        # Initializes by updating from prior assumption that object is at 0 position, velocity,
        # and acceleration, then subsequently updating using measurement
        self._t = init_timestamp
        self._x: Tensor = np.array(
            [list(init_measurement.position.as_tuple()), [0, 0, 0], [0, 0, 0]]
        )
        self._s: Tensor = var_to_covar(
            np.array(
                [
                    # Max uncertainty
                    np.diag(init_measurement.uncertainty.covariance).tolist(),
                    config.initial_derivative_variance[:3],
                    config.initial_derivative_variance[3:],
                ]
            )
        )

        self.update_from_new_position_measurement(init_measurement, init_timestamp)

    @property
    def latest_estimated_position(self) -> Position[WorldFrame]:
        """
        The position estimated at the time of the most recent update.
        """
        return Position(*self._x[0, :])

    @property
    def latest_estimated_velocity(self) -> Vector[WorldFrame]:
        """
        The velocity estimated at the time of the most recent update.
        """
        return Vector(*self._x[1, :])

    @property
    def latest_update_timestamp(self) -> JetsonTimestamp:
        """
        The time at which this target was most recently updated.
        """
        return self._t

    @property
    def latest_uncertainty(self) -> Vector[WorldFrame]:
        """
        Property getter.

        Returns:
            The current uncertainty from the most recent update.
        """
        return Vector.from_values(np.diag(self._s[0, :, 0, :]))

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

        prior = Estimation(self._x, self._s)

        prediction = self._k_filter.predict(
            prior, self._evolution_map(taylor_tensor), self._evolution_noise(taylor_tensor)
        )

        return Position(*prediction.expectation[0, :])

    def update_from_new_position_measurement(
        self, measurement: MeasuredPosition[WorldFrame], timestamp: JetsonTimestamp
    ):
        """
        Updates position, velocity, and acceleration using measured position and timestamp.

        Args:
            position: the newly measured position.
            timestamp: the time to update to.
        """
        super().update_from_new_position_measurement(measurement, timestamp)

        dt = (timestamp - self._t).duration_seconds

        taylor_tensor = self._taylor_tensor(dt)

        prior = Estimation(self._x, self._s)
        position_tensor: Tensor = np.array(measurement.position.as_tuple())

        new_estimate = self._k_filter.update(
            prior,
            self._evolution_map(taylor_tensor),
            self._evolution_noise(taylor_tensor),
            position_tensor,
            measurement.uncertainty.covariance,
        )

        self._t = timestamp
        self._x = new_estimate.expectation
        self._s = new_estimate.covariance

        if np.max(self._s) > COVARIANCE_WARNING_THRESHOLD:
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

        prior = Estimation(self._x, self._s)

        prediction = self._k_filter.predict(
            prior, self._evolution_map(taylor_tensor), self._evolution_noise(taylor_tensor)
        )

        self._t = timestamp
        self._x = prediction.expectation
        self._s = prediction.covariance
        if np.max(self._s) > COVARIANCE_WARNING_THRESHOLD:
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
        taylor: Tensor = np.zeros(2 * self._k_filter.state_shape)
        p: Tensor = np.ones((taylor.shape[0],))

        for i in range(1, taylor.shape[0]):
            p[i] = dt * p[i - 1] / i

        for i in range(taylor.shape[0]):
            for k in range(i, taylor.shape[0]):
                for j in range(taylor.shape[1]):
                    taylor[i, j, k, j] = p[k - i]

        return taylor

    def _evolution_map(self, taylor: Tensor) -> Tensor:
        """
        Uses taylor tensor to calculate evolution map.
        """
        evol_map: Tensor = taylor.copy()
        evol_map[-1, :, :-1, :] = self._ode_coefficients
        evol_map[-1, :, -1, :] = 0

        return evol_map

    def _evolution_noise(self, taylor: Tensor) -> Tensor:
        """
        Uses taylor tensor to calculate expected evolution noise.
        """
        noise: Tensor = np.einsum("ijkl,kl,mnkl->ijmn", taylor, self._intrinsic_noise, taylor)

        return noise


def var_to_covar(var: Tensor):
    """
    Helper function converts a variance tensor into a covariance matrix assuming no correlation.
    """
    return np.einsum(
        "ij,ik,jl,im,jn->klmn",
        var,
        np.eye(var.shape[0]),
        np.eye(var.shape[1]),
        np.eye(var.shape[0]),
        np.eye(var.shape[1]),
    )
