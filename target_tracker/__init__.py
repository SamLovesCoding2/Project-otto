"""
An empty abstract class TrackedTarget.

All the method besides the constructor will
throw a NotImplementedError exception. This class stores and updates
passed in position, time_stamp, velocity.
"""

from ._config import TargetConfiguration, TrackerConfiguration
from ._cv_kalman_tracked_target import OpenCVKalmanTrackedTarget
from ._kalman_tracked_target import KalmanTrackedTarget
from ._target_tracker import TargetTracker
from ._tracked_target import TrackedTarget

__all__ = [
    "OpenCVKalmanTrackedTarget",
    "KalmanTrackedTarget",
    "TargetTracker",
    "TrackedTarget",
    "TargetConfiguration",
    "TrackerConfiguration",
]
