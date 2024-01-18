import math
from dataclasses import dataclass
from typing import Any, Collection, Generic, Tuple, Type, TypeVar, overload

from project_otto.config_deserialization import PrimitiveConfigType
from project_otto.config_deserialization.utilities import assert_is_list

from ._frame import Frame
from ._vector import Vector

InFrame = TypeVar("InFrame", bound="Frame")


@dataclass(frozen=True)
class Position(Generic[InFrame]):
    """
    Represents a point in 3D space.

    Points are described by a three-tuple ``(x, y, z)``.

    A point exists in some chosen reference frame. See the documentation for the overall
    "spatial" module for more information.

    Args:
        x: X-coordinate of this Position (Forward/Backward)
        y: Y-coordinate of this Position (Left/Right)
        z: Z-coordinate of this Position (Up/Down)
    """

    x: float
    y: float
    z: float

    def as_tuple(self) -> Tuple[float, float, float]:
        """
        Extract the raw values associated with this Position.

        This function should be avoided when possible, as it loses frame-correctness guarantees. If
        possible, perform operations via a Transform such that they retain the associated reference
        frame of involved values.

        Returns:
            The represented position as a tuple of the form ``(x, y, z)``.
        """
        return (
            self.x,
            self.y,
            self.z,
        )

    @staticmethod
    def interpolate(
        alpha: float, xs: Tuple["Position[InFrame]", "Position[InFrame]"]
    ) -> "Position[InFrame]":
        """Returns: the position obtained by linearly interpolating between xs_0 and xs_1."""
        a, b = xs
        a_weight, b_weight = 1.0 - alpha, alpha
        return Position.from_values(
            [a_weight * a_i + b_weight * b_i for a_i, b_i in zip(a.as_tuple(), b.as_tuple())]
        )

    @staticmethod
    def mean(a: "Position[InFrame]", b: "Position[InFrame]") -> "Position[InFrame]":
        """Returns: the mean of a and b."""
        return Position.interpolate(0.5, (a, b))

    @staticmethod
    def distance(a: "Position[InFrame]", b: "Position[InFrame]") -> float:
        """Returns: the distance between of a and b."""
        return math.sqrt(sum([(a_i - b_i) ** 2 for a_i, b_i in zip(a.as_tuple(), b.as_tuple())]))

    @staticmethod
    def from_values(
        values: Collection[float], in_frame: Type[InFrame] = Any
    ) -> "Position[InFrame]":
        """
        Construct a Position from the passed collection of float "values".

        Args:
            values: a three-element tuple, list, numpy array, or other iterable collection. Provided
                values are interpreted in the order ``(x, y, z)``.
            in_frame: An optional type hint (class type) to constrain the frame of the returned
                Position.
        """
        if len(values) != 3:
            raise ValueError(
                "expected position as a three-tuple (x, y, z), "
                + f"got object with length {len(values)}"
            )

        values_tuple = tuple(values)
        return Position(values_tuple[0], values_tuple[1], values_tuple[2])

    @staticmethod
    def of_origin() -> "Position[InFrame]":
        """
        Returns a Position with zeroes in all axes.
        """
        return Position[InFrame](0, 0, 0)

    def __add__(self, vector: Vector[InFrame]) -> "Position[InFrame]":
        """
        Returns the Position given by adding a given Vector ``vector`` to this Position.

        Args:
            vector: the Vector to add to this position

        Returns:
            The resulting position of adding the Vector ``vector`` to this Position.

        """
        return Position(self.x + vector.x, self.y + vector.y, self.z + vector.z)

    def __radd__(self, vector: Vector[InFrame]) -> "Position[InFrame]":
        """
        Commutative mirror of ``__add__``.
        """
        return self + vector

    @overload
    def __sub__(self, other: "Position[InFrame]") -> Vector[InFrame]:
        """
        Overloaded __sub__ method.
        """
        ...

    @overload
    def __sub__(self, other: Vector[InFrame]) -> "Position[InFrame]":
        """
        Overloaded __sub__ method.
        """
        ...

    def __sub__(self, other: Any):
        """
        Overloads the "-" operator, allowing Vectors/Positions to be subtracted.

        The operation is overloaded for two types, subtracting a Position and subtracting a
        Timestamp.
        Returns the Position given by subtracting a given Vector from this Position.

        Args:
            other: either the Vector or Position to be subtracted from this Position

        Returns:
            If a Vector is passed in, returns the resulting Position from subtracting a Vector
            from this position.
            If a Position is passed in, returns a Vector representing the difference between this
            position and the passed position.
        """
        if isinstance(other, self.__class__):
            return Vector[InFrame](self.x - other.x, self.y - other.y, self.z - other.z)
        elif isinstance(other, Vector):
            return Position[InFrame](self.x - other.x, self.y - other.y, self.z - other.z)
        else:
            return NotImplemented

    @classmethod
    def parse_from_config_primitive(cls, value: PrimitiveConfigType) -> "Position[InFrame]":
        """
        Returns a Position interpretation of the given human-readable value.

        Expects a three-length list of coordinates.

        Raises:
            ValueError: if the value is illegal
        """
        values_list = assert_is_list(value, float)
        return Position.from_values(values_list)
