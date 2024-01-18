from dataclasses import dataclass
from typing import Generic, TypeVar

import numpy as np
import numpy.typing as npt

from ._frame import Frame

NUM_SPATIAL_DIMS = 3

InFrame = TypeVar("InFrame", bound="Frame")


@dataclass(frozen=True)
class LinearUncertainty(Generic[InFrame]):
    """
    Three-dimensional uncertainty, represented as a covariance matrix.

    Intended for positions and vectors in 3D space.
    """

    covariance: npt.NDArray[np.float64]

    @classmethod
    def from_variances(
        cls, x_variance: float, y_variance: float, z_variance: float
    ) -> "LinearUncertainty[InFrame]":
        """
        Constructs a LinearUncertainty described by a diagonal covariance matrix.
        """
        return LinearUncertainty(
            np.diag(np.array([x_variance, y_variance, z_variance], dtype=np.float64))
        )

    def __post_init__(self):
        """
        Post-init validation.
        """
        height, width = self.covariance.shape

        if height != NUM_SPATIAL_DIMS or width != NUM_SPATIAL_DIMS:
            raise ValueError(
                f"LinearUncertainty requires 3x3 covariance matrix, got {height}x{width}"
            )

    def __hash__(self):
        """
        Hash function.

        NumPy arrays and Python lists do not support hashing, so we build tuples.
        """
        return hash((self.covariance.shape, tuple(self.covariance.flatten().tolist())))
