from dataclasses import dataclass
from typing import List, Tuple

import numpy as np
import numpy.typing as npt

from project_otto.time import Duration

Tensor = npt.NDArray[np.float64]


def assert_shape_equals(tensor_name: str, shape: Tuple[int, ...], expected_shape: Tuple[int, ...]):
    """Shortcut for tensor shape-checking."""
    if shape != expected_shape:
        raise ValueError(f"Expected tensor {tensor_name} of shape {expected_shape}, got {shape}.")


@dataclass
class TargetConfiguration:
    """
    Config class for TrackedTarget.

    Args:
        num_independent_vars: Number of state variables, i.e., independent variables in the
            system. (n)
        num_derivatives: Highest differentiation order to track for each state variable. (m)
        num_measured_vars: Number of variables being measured. (k)
        initial_derivative_variance: initial variance values assigned to each of the derivatives.
        ode_coefficients: (n, m, n) shape tensor. The ijk-th term gives the coefficient for the
            j-th derivative of the k-th variable on the m-th derivative of the i-th variable.
        intrinsic_noise: (m + 1, n) shape tensor. The ij-th term gives the variance of real systemic
            noise for the i-th derivative of the j-th variable.
        measurement_map: (k, m + 1, n) shape tensor. Linear map from the (m + 1, n) shape state to
            the (k,) shape measurement.
    """

    num_independent_vars: int
    num_derivatives: int
    num_measured_vars: int
    initial_derivative_variance: List[float]
    ode_coefficients: Tensor
    intrinsic_noise: Tensor
    measurement_map: Tensor

    def __post_init__(self):
        """
        Validates config attributes.
        """
        m = (self.num_independent_vars, self.num_derivatives, self.num_independent_vars)
        n = (self.num_derivatives + 1, self.num_independent_vars)
        k = (self.num_measured_vars,)
        assert_shape_equals("ode_coefficients", self.ode_coefficients.shape, m)
        assert_shape_equals("intrinsic_noise", self.intrinsic_noise.shape, n)
        assert_shape_equals("measurement_map", self.measurement_map.shape, k + n)

        if np.any(self.intrinsic_noise < 0):
            raise ValueError("Expected intrinsic_noise to have non-negative entries.")


@dataclass
class TrackerConfiguration:
    """
    Config class for tracker.

    Args:
        max_distance: An assumed bound for velocity a target can go, used to determine max distance
            when correlating old and new targets.
        max_staleness: Duration of time a target will remain tracked without being correlated with a
            measured target.
    """

    max_distance: float
    max_staleness: Duration
