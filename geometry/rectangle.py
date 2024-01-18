"""A Generic 2D Rectangle."""
from dataclasses import dataclass
from typing import Generic, TypeVar

from project_otto.geometry.point import Point

T = TypeVar("T", int, float)


@dataclass(frozen=True)
class Rectangle(Generic[T]):
    """
    A 2D rectangle, represented as the top-left ``(x0, y0)`` and bottom-right ``(x1, y1)`` points.

    Args:
        x0: The X-coordinate of the top-left corner.
        y0: The Y-coordinate of the top-left corner.
        x1: The X-coordinate of the bottom-right corner.
        y1: The Y-coordinate of the bottom-right corner.
    """

    x0: T
    y0: T
    x1: T
    y1: T

    def __post_init__(self):
        """post-init hook for the @dataclass's generated __init__ function."""
        if self.x1 < self.x0:
            raise ValueError(f"Expected x0 < x1, got x0 = {self.x0}, x1 = {self.x1}")
        if self.y1 < self.y0:
            raise ValueError(f"Expected y0 < y1, got y0 = {self.y0}, y1 = {self.y1}")

    @classmethod
    def from_point(cls, top_left: Point[T], width: T, height: T):
        """
        Creates a new Rectangle, described by the top-left point, width, and height.

        Args:
            top_left: A :class:`Point` defining the rectangle's top-left corner.
            width: The rectangle's width.
            height: The rectangle's height.
        """
        return cls(top_left.x, top_left.y, top_left.x + width, top_left.y + height)

    @property
    def center(self) -> Point[float]:
        """A point corresponding to the center of the rectangle."""
        return Point[float]((self.x0 + self.x1) / 2, (self.y0 + self.y1) / 2)

    @property
    def top_left(self) -> Point[T]:
        """A point corresponding to the top left vertex of the rectangle."""
        return Point[T](self.x0, self.y0)

    @property
    def bottom_right(self) -> Point[T]:
        """A point corresponding to the bottom right vertex of the rectangle."""
        return Point[T](self.x1, self.y1)

    @property
    def width(self) -> T:
        """The width of the rectangle."""
        return self.x1 - self.x0

    @property
    def height(self) -> T:
        """The height of the rectangle."""
        return self.y1 - self.y0

    @property
    def area(self) -> T:
        """The area of the rectangle."""
        return self.width * self.height

    @staticmethod
    def iou(a: "Rectangle[T]", b: "Rectangle[T]") -> float:
        """The area of the intersection of a and b divided by the area of their union."""
        x_overlap = max(0, min(a.x1, b.x1) - max(a.x0, b.x0))
        y_overlap = max(0, min(a.y1, b.y1) - max(a.y0, b.y0))
        intersection = x_overlap * y_overlap
        union = a.area + b.area - intersection
        return intersection / union


FloatRectangle = Rectangle[float]
IntRectangle = Rectangle[int]
