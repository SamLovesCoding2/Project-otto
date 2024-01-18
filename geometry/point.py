"""Generic 2D Point."""
from dataclasses import dataclass
from typing import Generic, TypeVar

T = TypeVar("T", int, float)


@dataclass
class Point(Generic[T]):
    """A 2D Point, represented by coordinates ``(x, y)``."""

    x: T
    y: T


FloatPoint = Point[float]
IntPoint = Point[int]
