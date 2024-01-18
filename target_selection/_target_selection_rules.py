import math
from abc import ABC, abstractmethod
from typing import Optional

from project_otto.frames import LauncherFrame
from project_otto.spatial import Position
from project_otto.target_tracker import TrackedTarget
from project_otto.transform_providers import WorldFrameToLauncherFrameTransformProvider


class TargetSelectionRule(ABC):
    """
    Abstract class for target selection rules.
    """

    @abstractmethod
    def get_score(self, target: TrackedTarget) -> Optional[float]:
        """
        Compute the target score for aiming based on the rules, ranging from 0 to 100.

        Higher scores indicate less desirability to shoot at. None will be returned to disqualify
        a target from being aimed at.

        Args:
            A target in WorldFrame to evaluate.
        Returns:
            The score of the target based on selected rules, None if target should be invalid.
        """
        pass


class TurretRotationDifferenceRule(TargetSelectionRule):
    """
    Rule based on rotational distance between target and the turret.

    Args:
        turret_transform_provider: a Transform Provider indicating the position of the turret
    """

    def __init__(self, turret_transform_provider: WorldFrameToLauncherFrameTransformProvider):
        self._turret_transform_provider = turret_transform_provider

    def get_score(self, target: TrackedTarget) -> Optional[float]:
        """
        Calculate the aiming score of the given target.

        The aiming score represents how much the turret would have to rotate to aim at the target.
        In the worst case, the score returned would be 100, which means the turret would have to
        rotate 180 degrees to aim at the target.

        Args:
            target: A target object in the WorldFrame to evaluate.

        Returns:
            A float value that ranges from 0 to 100. The higher the value is, the worse the target
            is.
        """
        transform = self._turret_transform_provider.world_frame_to_launcher_frame_transform
        turret_relative_position = transform.apply_to_position(target.latest_estimated_position)
        distance_from_turret = Position.distance(turret_relative_position, Position(0, 0, 0))
        distance_along_forward_direction = turret_relative_position.x

        if distance_from_turret == 0:
            return 0

        target_angle_score_from_turret_center = (
            math.acos(distance_along_forward_direction / distance_from_turret) * 100 / math.pi
        )
        return target_angle_score_from_turret_center


class TurretDistanceRule(TargetSelectionRule):
    """
    Rule based on distance between target and turret.

    Args:
        max_distance: Maximum distance beyond which targets are not considered.
        turret_transform_provider: a Transform Provider indicating the position of the turret
    """

    def __init__(
        self,
        max_distance: float,
        turret_transform_provider: WorldFrameToLauncherFrameTransformProvider,
    ):
        self._max_distance = max_distance
        self._turret_transform_provider = turret_transform_provider

    def get_score(self, target: TrackedTarget) -> Optional[float]:
        """
        Calculate the distance score of the given target.

        The distance score represents how difficult the target is to aim at based on the distance
        from the target to the turret.
        If the target is more than MAX_DISTANCE meters from turret, None will be returned
        representing the target is invalid.

        Args:
            target: A target object in the WorldFrame to evaluate.

        Returns:
            A float value that ranges from 0 to 100. The higher the value is, the worse the target
            is. None if the target is invalid.
        """
        transform = self._turret_transform_provider.world_frame_to_launcher_frame_transform
        turret_relative_position = transform.apply_to_position(target.latest_estimated_position)
        distance_from_turret = Position.distance(
            turret_relative_position, Position[LauncherFrame].of_origin()
        )

        if distance_from_turret > self._max_distance:
            return None

        return (distance_from_turret / self._max_distance) * 100


class IdentityRule(TargetSelectionRule):
    """
    Rule based on the identity of the target.
    """

    def __init__(self, target: Optional[TrackedTarget]):
        self._target = target

    def get_score(self, target: TrackedTarget) -> float:
        """
        Scores the given target.

        Returns 0 if the given target is the stored target, and 1 if not. Compares with object
        identity.
        """
        return float(self._target is not target)
