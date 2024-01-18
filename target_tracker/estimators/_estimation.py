from dataclasses import dataclass
from typing import Tuple

import numpy as np
import numpy.typing as npt

Tensor = npt.NDArray[np.float64]


def assert_valid_covariance(tensor_name: str, tensor: Tensor):
    """Shortcut for covariance property checking."""
    flattened_tensor: Tensor = np.reshape(tensor, 2 * (int(np.sqrt(np.prod(tensor.shape))),))
    if np.any(np.linalg.eigvals(flattened_tensor) < 0):
        raise InvalidCovariancePosSemiDefiniteError(tensor_name)
    if not np.allclose(flattened_tensor, np.transpose(flattened_tensor)):
        raise InvalidCovarianceAsymmetricError(tensor_name)


@dataclass
class Estimation:
    """
    Normally distributed estimation of a system of variables.
    """

    expectation: Tensor
    covariance: Tensor

    def __post_init__(self):
        """
        Validates state-covariance pair.
        """
        if self.covariance.shape != 2 * self.expectation.shape:
            raise ValueError(
                f"Expected covariance of shape {2 * self.expectation.shape}, got "
                + f"{self.covariance.shape}."
            )
        assert_valid_covariance("covariance", self.covariance)

    def as_tuple(self):
        """
        Returns self as a tuple of state and covariance.
        """
        return self.expectation, self.covariance


def nearest_valid_covariance(covariance: Tensor) -> Tensor:
    """
    Function which corrects internal covariance against floating point errors via polar decomp.
    """
    flattened_covariance: Tensor = np.reshape(
        covariance, 2 * (int(np.sqrt(np.prod(covariance.shape))),)
    )
    symmetric_covariance = 0.5 * (flattened_covariance + np.transpose(flattened_covariance))
    decomp: Tuple[Tensor, Tensor, Tensor] = np.linalg.svd(symmetric_covariance, hermitian=True)
    almost_symmetric_polar_factor = np.matmul(
        np.transpose(decomp[2]), np.matmul(np.diag(decomp[1]), decomp[2])
    )
    symmetric_polar_factor = 0.5 * (
        almost_symmetric_polar_factor + np.transpose(almost_symmetric_polar_factor)
    )
    flattened_valid_covariance = 0.5 * (symmetric_covariance + symmetric_polar_factor)
    valid_covariance: Tensor = np.reshape(flattened_valid_covariance, covariance.shape)
    return valid_covariance


class InvalidCovariancePosSemiDefiniteError(Exception):
    """Exception raised when given array for covariance has negative entries in diagonal."""

    def __init__(self, tensor_name: str):
        super().__init__(f"Expected tensor {tensor_name} to be positive semi-definite.")


class InvalidCovarianceAsymmetricError(Exception):
    """Exception raised when given array for covariance is asymmetric."""

    def __init__(self, tensor_name: str):
        super().__init__(f"Expected tensor {tensor_name} to be symmetric.")
