import abc
from dataclasses import dataclass
from typing import Any, Generic, TypeVar

import numpy as np
import numpy.typing as npt

from project_otto.geometry import Point, Rectangle
from project_otto.spatial import Frame, Position
from project_otto.time import TimeDomain, Timestamp

InFrame = TypeVar("InFrame", bound="Frame", covariant=True)
TimeType = TypeVar("TimeType", bound="Timestamp[TimeDomain]", covariant=True)

NumpyDataType = TypeVar("NumpyDataType", np.uint8, np.uint16)


# Helper function
def _subsection(
    arr: npt.NDArray[NumpyDataType], rect: Rectangle[int]
) -> npt.NDArray[NumpyDataType]:
    """Returns a subsection of the array `arr` bounded by `rect`."""
    if rect.x0 < 0:
        raise IndexError("Expected non-negative x0, got " + str(rect.x0))
    if rect.y0 < 0:
        raise IndexError("Expected non-negative y0, got " + str(rect.y0))

    arr_height, arr_width = arr.shape[:2]
    if rect.x1 > arr_width:
        raise IndexError(f"Expected x1 less than or equal to {arr_width}, got {rect.x1}")
    if rect.y1 > arr_height:
        raise IndexError(f"Expected y1 less than or equal to {arr_height}, got {rect.y1}")

    return arr[rect.y0 : rect.y1, rect.x0 : rect.x1]


@dataclass
class Frameset(Generic[InFrame, TimeType], metaclass=abc.ABCMeta):
    """
    A set of frames captured at the same timestamp.

    Args:
        color: The color frame.
        depth: The depth frame.
        time: The timestamp these frames were captured.
    """

    color: npt.NDArray[np.uint8]
    depth: npt.NDArray[np.uint16]
    time: TimeType
    intrinsics: Any  # TODO: replace with wrapper (probably will have a generic dummy interface one)

    def subsection_color(self, rect: Rectangle[int]) -> npt.NDArray[np.uint8]:
        """
        Returns a subsection of the color array bounded by `rect`.

        The column specified by the right coordinate, and the row specified by the bottom one, are
        *not* included in the cropped result. i.e., the rightmost and bottommost bounds are
        *exclusive* while the leftmost and rightmost are inclusive.
        """
        return _subsection(self.color, rect)

    def subsection_depth(self, rect: Rectangle[int]) -> npt.NDArray[np.uint16]:
        """
        Returns a subsection of the depth array bounded by `rect`.

        The column specified by the right coordinate, and the row specified by the bottom one, are
        *not* included in the cropped result. i.e., the rightmost and bottommost bounds are
        *exclusive* while the leftmost and rightmost are inclusive.
        """
        return _subsection(self.depth, rect)

    @abc.abstractmethod
    def position_to_point(self, pos: Position[InFrame]) -> Point[Any]:
        """
        Returns the 2D point in this frame at which the specified 3D position `pos` would appear.
        """
        pass

    @abc.abstractmethod
    def point_to_position(self, pt: Point[Any], depth: float) -> Position[InFrame]:
        """
        Converts and returns a 2D point on the image into a 3D position.
        """
        pass
