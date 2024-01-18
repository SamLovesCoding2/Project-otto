from typing import Tuple

import numpy as np
import numpy.typing as npt

from project_otto.target_tracker.estimators._estimation import (
    Estimation,
    assert_valid_covariance,
    nearest_valid_covariance,
)

Tensor = npt.NDArray[np.float64]


def assert_shape_equals(tensor_name: str, shape: Tuple[int, ...], expected_shape: Tuple[int, ...]):
    """Shortcut for tensor shape-checking."""
    if shape != expected_shape:
        raise ValueError(f"Expected tensor {tensor_name} of shape {expected_shape}, got {shape}.")


class KalmanFilter:
    """
    Kalman filter that admits variable evolution and evolution noise.

    Args:
        state_shape: Shape of state tensor.
        measurement_shape: Shape of measurement tensor.
        measurement_map: Tensor of shape n+k giving the mapping from the state to the measurement.
    """

    def __init__(
        self,
        state_shape: Tuple[int, ...],
        measurement_shape: Tuple[int, ...],
        measurement_map: Tensor,
    ):

        # Shape of variables
        self._n = state_shape

        # Shape of observed variables
        self._k = measurement_shape

        # Measurement tensor
        assert_shape_equals("measurement_shape", measurement_map.shape, self._k + self._n)
        self._measurement_map = measurement_map

    @property
    def state_shape(self) -> Tuple[int, ...]:
        """
        Returns the shape of the tensor containing the system variables that are being estimated.
        """
        return self._n

    @property
    def measurement_shape(self) -> Tuple[int, ...]:
        """
        Returns the expected shape of incoming tensors containing the measured variables.
        """
        return self._k

    def predict(self, prior: Estimation, evol_map: Tensor, evol_noise: Tensor) -> Estimation:
        """
        Returns an estimate of the next state using provided evolution tensors.

        Args:
            prior: The previous estimate.
            evol_map: The linear map from the previous estimate to the next estimate.
            evol_noise: The covariance representing the noise of the system evolution.
        Returns:
            State and covariance tensors.
        """
        assert_shape_equals("prior.state", prior.expectation.shape, self._n)
        # Covariance implicitly checked by above line
        assert_shape_equals("evol_transform", evol_map.shape, 2 * self._n)
        assert_shape_equals("evol_noise", evol_noise.shape, 2 * self._n)

        # Flatten to allow for einsum over arbitrary tensor shapes
        estimation_f: Tensor = np.reshape(prior.expectation, (np.prod(self._n),))
        covariance_f: Tensor = np.reshape(prior.covariance, 2 * (np.prod(self._n),))
        transform_f: Tensor = np.reshape(evol_map, 2 * (np.prod(self._n),))

        # Apply differential equation to X and C
        x: Tensor = np.reshape(np.einsum("ij,j->i", transform_f, estimation_f), self._n)
        s: Tensor = (
            np.reshape(
                nearest_valid_covariance(
                    np.einsum("ij,jk,lk->il", transform_f, covariance_f, transform_f)
                ),
                2 * self._n,
            )
            + evol_noise
        )

        return Estimation(x, s)

    def filter(
        self, prediction: Estimation, measurement: Tensor, measurement_covariance: Tensor
    ) -> Estimation:
        """
        Returns a filtered estimation which combines the prediction with the measurement.

        Args:
            prediction: The prediction based on prior knowledge about the system.
            measurement: The new measurement.
        """
        assert_shape_equals("prediction.state", prediction.expectation.shape, self._n)
        assert_shape_equals("measurement", measurement.shape, self._k)
        assert_shape_equals("measurement_covariance", measurement_covariance.shape, 2 * self._k)
        assert_valid_covariance("measurement_covariance", measurement_covariance)

        # Flatten to allow for einsum over arbitrary tensor shapes
        h: Tensor = np.reshape(self._measurement_map, (np.prod(self._k), np.prod(self._n)))
        r: Tensor = np.reshape(measurement_covariance, 2 * (np.prod(self._k),))
        x: Tensor = np.reshape(prediction.expectation, (np.prod(self._n),))
        s: Tensor = np.reshape(prediction.covariance, 2 * (np.prod(self._n),))

        # Get measurement residual and its covariance (pre-fit)
        y: Tensor = measurement - np.einsum("ij,j->i", h, x)
        d: Tensor = np.einsum("ij,jk,lk->il", h, s, h) + r

        # Calculate optimal Kalman gain
        k: Tensor = np.einsum("ij,kj,kl->il", s, h, np.linalg.inv(d))

        # Fit prediction to observation
        x: Tensor = np.reshape(x + np.einsum("ij,j->i", k, y), self._n)
        s: Tensor = np.reshape(
            nearest_valid_covariance(s - np.einsum("ij,jk,kl->il", k, h, s)), 2 * self._n
        )

        return Estimation(x, s)

    def update(
        self,
        prior: Estimation,
        evol_tensor: Tensor,
        evol_noise: Tensor,
        measurement: Tensor,
        measurement_covariance: Tensor,
    ) -> Estimation:
        """
        Full update step.

        Makes a prediction and then filters it. Returns result.
        """
        return self.filter(
            self.predict(prior, evol_tensor, evol_noise), measurement, measurement_covariance
        )
