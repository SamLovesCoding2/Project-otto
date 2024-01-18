"""Classes and interfaces relating to detecting targets."""

from ._aruco_detector import ArucoDetector
from ._camera_relative_detected_target_set import (
    CameraRelativeDetectedTargetSet,
    TargetProjectionUncertaintyConfig,
)
from ._config import DetectorConfiguration
from ._target import DetectedTargetPosition, DetectedTargetRegion
from ._target_detector import LightningTargetDetector, TargetDetector
from ._target_prune import prune_invalid_targets
from ._target_prune_configuration import TargetPruneConfiguration
from ._target_set import ImageDetectedTargetSet
from ._world_detected_target_set import WorldDetectedTargetSet

__all__ = [
    "ArucoDetector",
    "CameraRelativeDetectedTargetSet",
    "TargetProjectionUncertaintyConfig",
    "DetectorConfiguration",
    "DetectedTargetPosition",
    "DetectedTargetRegion",
    "ImageDetectedTargetSet",
    "LightningTargetDetector",
    "prune_invalid_targets",
    "TargetDetector",
    "TargetPruneConfiguration",
    "prune_invalid_targets",
    "WorldDetectedTargetSet",
]
