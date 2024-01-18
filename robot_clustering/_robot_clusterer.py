from typing import Generic, List, TypeVar

from project_otto.frames import WorldFrame
from project_otto.spatial import Position
from project_otto.target_tracker import TrackedTarget
from project_otto.timestamps import JetsonTimestamp

from ._config import RobotClustererConfiguration
from ._target_grouper import TargetGrouper
from ._variable_k_means import VariableKMeans

InTrackedTarget = TypeVar("InTrackedTarget", bound="TrackedTarget")


class RobotClusterer(Generic[InTrackedTarget]):
    """
    Represents the robot tracker state.

    Args:
        target_grouper: the target matcher to use for target pairing and center estimation.
        variable_k_means: the tracked centers.
    """

    _target_grouper: TargetGrouper[InTrackedTarget]
    _variable_k_means: VariableKMeans

    def __init__(
        self,
        target_grouper: TargetGrouper[InTrackedTarget],
        variable_k_means: VariableKMeans,
    ):
        self._target_grouper = target_grouper
        self._variable_k_means = variable_k_means

    def update(self, targets: List[InTrackedTarget], current_time: JetsonTimestamp):
        """
        Updates the tracked center estimates using the passed target list.

        Args:
            targets: a list of observed targets.
        """
        grouped_target_positions = self._target_grouper.group_targets(targets)
        self._variable_k_means.update(grouped_target_positions, current_time)

    @property
    def centers(self) -> List[Position[WorldFrame]]:
        """
        Returns: the current tracked center estimates.
        """
        return self._variable_k_means.centers

    @classmethod
    def from_config(cls, config: RobotClustererConfiguration) -> "RobotClusterer[InTrackedTarget]":
        """Constructs a robot tracker from the provided config."""
        return cls(
            TargetGrouper(config.min_radius, config.max_radius),
            VariableKMeans(config.age_limit, config.interpolation_coefficient, config.max_radius),
        )
