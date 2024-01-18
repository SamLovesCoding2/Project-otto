import math
from dataclasses import dataclass
from typing import Any, Collection, Generic, Tuple, Type, TypeVar

from ._frame import Frame

InFrame = TypeVar("InFrame", bound="Frame")


@dataclass
class Vector(Generic[InFrame]):
    """
    Represents a three-dimensional non-positional quantity in some specified reference frame.

    Vectors are similar to Positions in structure; they are equivalent to a three-tuple
    ``(x, y, z)``. However, when a transform between spatial reference frames is applied, a Vector's
    overall magnitude is unaffected; only its directionality changes. The magnitude of a Vector is
    assumed to be unrelated to physical distances.

    Vectors are intended to represent measurements such as 3D velocities or accelerations.

    A vector exists in some chosen reference frame. See the documentation for the overall
    "spatial" module for more information.

    Args:
        x: X-coordinate of this Vector
        y: Y-coordinate of this Vector
        z: Z-coordinate of this Vector
    """

    x: float
    y: float
    z: float

    def as_tuple(self) -> Tuple[float, float, float]:
        """
        Extract the raw values associated with this Vector.

        This function should be avoided when possible, as it loses frame-correctness guarantees. If
        possible, perform operations via a Transform such that they retain the associated reference
        frame of involved values.

        Returns:
            Return the represented vector as a tuple of the form ``(x, y, z)``.
        """
        return (
            self.x,
            self.y,
            self.z,
        )

    @staticmethod
    def from_values(values: Collection[float], in_frame: Type[InFrame] = Any) -> "Vector[InFrame]":
        """
        Construct a Vector from the passed collection of float "values".

        Args:
            values: a three-element tuple, list, numpy array, or other iterable collection. Provided
                values are interpreted in the order ``(x, y, z)``.
            in_frame: An optional type hint (class type) to constrain the frame of the returned
                Position.
        """
        if len(values) != 3:
            raise ValueError(
                f"expected vector as a three-tuple (x, y, z), got object with length {len(values)}"
            )

        values_tuple = tuple(values)
        return Vector(values_tuple[0], values_tuple[1], values_tuple[2])

    def __add__(self, vector: Any) -> "Vector[InFrame]":
        """
        Returns the Vector given by adding a given Vector ``vector`` to this Vector.

        Args:
            vector: the Vector to add to this vector

        Returns:
            The resulting vector of adding the Vector ``vector`` to this Vector.

        """
        if not isinstance(vector, Vector):
            return NotImplemented
        return Vector(self.x + vector.x, self.y + vector.y, self.z + vector.z)

    def __sub__(self, vector: "Vector[InFrame]") -> "Vector[InFrame]":
        """
        Returns the Vector given by subtracting a given Vector ``vector`` to this Vector.

        Args:
            vector: the Vector to subtract from this vector.

        Returns:
            The resulting vector.
        """
        return Vector(self.x - vector.x, self.y - vector.y, self.z - vector.z)

    def __mul__(self, scalar: float) -> "Vector[InFrame]":
        """
        Returns the Vector given by element-wise multiplication.

        Args:
            scalar: the magnitude to scale this Vector by.
        Returns:
            The resulting Vector given by scalaing all 3 coordinates of this Vector by ''scalar``.

        """
        return Vector(self.x * scalar, self.y * scalar, self.z * scalar)

    def __rmul__(self, scalar: float) -> "Vector[InFrame]":
        """
        Commutative mirror of ``__add__``.
        """
        return self * scalar

    def __truediv__(self, divisor: float) -> "Vector[InFrame]":
        """
        Returns the Vector given by element-wise division.

        Args:
            divisor: the (non-zero) magnitude to divide all coordinates of this Vector by.
        Returns:
            The resulting Vector given by dividing all 3 coordinates of this Vector by ``divisor``.

        """
        if divisor == 0:
            raise ZeroDivisionError()

        return Vector(self.x / divisor, self.y / divisor, self.z / divisor)

    def magnitude(self) -> float:
        """
        Returns the magnitude of this vector.
        """
        return math.sqrt(self.x ** 2 + self.y ** 2 + self.z ** 2)
