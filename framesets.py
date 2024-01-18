"""
Frameset definitions specific to Project Otto.
"""
import abc
from typing import Any, Tuple

import pyrealsense2 as rs  # type: ignore

from project_otto.frames import ColorCameraFrame
from project_otto.geometry import Point
from project_otto.image import Frameset
from project_otto.spatial import Position
from project_otto.timestamps import JetsonTimestamp


def _rs2_project_point_to_pixel(
    intrinsics: Any, position: Tuple[float, float, float]
) -> Tuple[float, float]:
    return tuple(rs.rs2_project_point_to_pixel(intrinsics, position))  # type: ignore


def _rs2_deproject_pixel_to_point(
    intrinsics: Any, point: Tuple[int, int], depth: float
) -> Tuple[float, float, float]:
    return rs.rs2_deproject_pixel_to_point(intrinsics, point, depth)  # type: ignore


class RealsenseFrameset(Frameset[ColorCameraFrame, JetsonTimestamp], metaclass=abc.ABCMeta):
    """
    Frameset relative to ColorCameraFrame and JetsonTimestamp.
    """

    def position_to_point(self, pos: Position[ColorCameraFrame]) -> Point[float]:
        """
        Projects a 3d position to a 2d point.
        """
        # Convert from meters to millimeters before passing into rs2
        rs2_position = (-pos.y * 1000, -pos.z * 1000, pos.x * 1000)
        rs2_point = _rs2_project_point_to_pixel(self.intrinsics, rs2_position)
        return Point(rs2_point[0], rs2_point[1])

    def point_to_position(self, pt: Point[Any], depth: float) -> Position[ColorCameraFrame]:
        """
        Deprojects a 2d point with depth to a 3d position.
        """
        rs2_position: Any = _rs2_deproject_pixel_to_point(self.intrinsics, (pt.x, pt.y), depth)
        # Convert from rs2 output from millimeters to meters
        return Position[ColorCameraFrame](
            rs2_position[2] / 1000, -rs2_position[0] / 1000, -rs2_position[1] / 1000
        )
