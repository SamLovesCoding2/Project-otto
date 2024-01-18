"""Target set in the world frame."""
from dataclasses import dataclass
from typing import Set

from project_otto.frames import WorldFrame
from project_otto.timestamps import JetsonTimestamp, OdometryTimestamp
from project_otto.transform_providers import CameraFrameToWorldFrameTransformProvider

from ._camera_relative_detected_target_set import CameraRelativeDetectedTargetSet
from ._target import DetectedTargetPosition


@dataclass
class WorldDetectedTargetSet:
    """
    Target set of target regions in the world frame.
    """

    positions: Set[DetectedTargetPosition[WorldFrame]]
    jetson_timestamp: JetsonTimestamp
    odometry_timestamp: OdometryTimestamp

    @staticmethod
    def from_camera_relative(
        camera_relative_target_set: CameraRelativeDetectedTargetSet,
        to_world_transform_provider: CameraFrameToWorldFrameTransformProvider,
        odometry_timestamp: OdometryTimestamp,
    ) -> "WorldDetectedTargetSet":
        """
        Converts a set of targets detected in the frame relative to the camera to the world frame.

        Args:
            camera_relative_target_set: Set of detected target positions in the camera frame
            to_world_transform_provider: Guaranteed provider of transform from camera frame to world
            odometry_timestamp: timestamp to which the given transform provider corresponds
        """
        jetson_timestamp = camera_relative_target_set.timestamp
        to_world_transform = to_world_transform_provider.camera_frame_to_world_frame_transform

        positions = set(
            (
                DetectedTargetPosition(
                    target.confidence,
                    target.color,
                    to_world_transform.apply_to_measured_position(target.measurement),
                )
                for target in camera_relative_target_set.positions
            )
        )

        return WorldDetectedTargetSet(positions, jetson_timestamp, odometry_timestamp)
