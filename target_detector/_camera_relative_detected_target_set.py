"""Target set relative to the camera position."""
from dataclasses import dataclass
from typing import Any, Optional, Set, TypeVar

import numpy as np
import numpy.typing as npt

from project_otto.frames import ColorCameraFrame
from project_otto.image import Frameset
from project_otto.spatial import LinearUncertainty, MeasuredPosition, Position
from project_otto.time import Timestamp
from project_otto.timestamps import JetsonTimestamp

from ._target import DetectedTargetPosition
from ._target_set import ImageDetectedTargetSet

"""The proportion that the proportion of zeroes and NaN's to size of depth_rect is tested against"""
_MAX_INVALID_DEPTH_PERCENTAGE = 0.7

TimeType = TypeVar("TimeType", bound="Timestamp[Any]")


def _median_depth(depth_rect: npt.NDArray[np.uint16]) -> Optional[float]:
    """
    Calculates the median of the depth rectangle of an armor plate, ignoring zeros and NaN's.

    Args:
    depth_rect: The array that holds the depth values of a specific armor plate.
    """
    if depth_rect.size == 0:
        return None
    proportion_nan_zero = (
        np.isnan(depth_rect).sum() + np.count_nonzero(depth_rect == 0)
    ) / depth_rect.size
    if proportion_nan_zero > _MAX_INVALID_DEPTH_PERCENTAGE:
        return None
    # Throw out NaN's and zeroes before median calculation
    return float(np.nanmedian(depth_rect[depth_rect != 0]))


@dataclass
class TargetProjectionUncertaintyConfig:
    """
    Options to describe the approximate noise in observed input target measurements.
    """

    depth_stddev_per_meter: float
    position_stddev_per_meter: float


def _uncertainty_for_target(
    position: Position[ColorCameraFrame], config: TargetProjectionUncertaintyConfig
):
    distance = Position.distance(position, Position.of_origin())
    return LinearUncertainty[ColorCameraFrame].from_variances(
        (config.depth_stddev_per_meter * distance) ** 2,
        (config.position_stddev_per_meter * distance) ** 2,
        (config.position_stddev_per_meter * distance) ** 2,
    )


@dataclass
class CameraRelativeDetectedTargetSet:
    """Set of targets at a certain timestamp, including their Positions in InFrame."""

    positions: Set[DetectedTargetPosition[ColorCameraFrame]]
    timestamp: JetsonTimestamp

    @staticmethod
    def from_detected_rectangles(
        frameset: Frameset[ColorCameraFrame, JetsonTimestamp],
        target_set: ImageDetectedTargetSet,
        uncertainty_config: TargetProjectionUncertaintyConfig,
    ) -> "CameraRelativeDetectedTargetSet":
        """
        Create a set of 3D target :class:`~project_otto.spatial.Position` relative to the camera.

        Args:
            frameset: A set of color and depth frames from the RealSense at a certain timestamp.
            target_set: Set of detected 2D target regions.
        """
        positions: Set[DetectedTargetPosition[ColorCameraFrame]] = set()
        for target in target_set.plates:
            depth_rect = frameset.subsection_depth(target.rectangle)
            depth = _median_depth(depth_rect)
            if depth is not None:
                position = frameset.point_to_position(target.rectangle.center, depth)
                uncertainty = _uncertainty_for_target(position, uncertainty_config)

                positions.add(
                    DetectedTargetPosition(
                        target.detection_confidence,
                        target.color,
                        MeasuredPosition(position, uncertainty),
                    )
                )
        return CameraRelativeDetectedTargetSet(positions, frameset.time)
