from typing import Generic, List, MutableSet, TypeVar

from project_otto.frames import WorldFrame
from project_otto.spatial import Position
from project_otto.target_tracker import TrackedTarget

from ._timestamped_position import TimestampedPosition

InTrackedTarget = TypeVar("InTrackedTarget", bound="TrackedTarget")


class TargetGrouper(Generic[InTrackedTarget]):
    """
    Represents target grouping configuration for the purpose of center estimation.

    Centers are estimated by way of pairing targets further from eachother than min_radius
    and closer to eachother than max_radius and, subsequently, mapping target pairs to their
    respective means.

    Args:
        min_radius: the minimum distance allowed between paired plates.
        max_radius: the maximum distance allowed between paired plates.
    """

    _min_radius: float
    _max_radius: float

    def __init__(self, min_radius: float, max_radius: float):
        self._min_radius = min_radius
        self._max_radius = max_radius

    def _satisfactory(self, a: Position[WorldFrame], b: Position[WorldFrame]) -> bool:
        return self._min_radius <= Position.distance(a, b) <= self._max_radius

    def _retrieve_center_estimate(
        self,
        target: InTrackedTarget,
        targets_set: MutableSet[InTrackedTarget],
    ) -> TimestampedPosition:
        satisfying_targets = [
            x
            for x in targets_set
            if self._satisfactory(target.latest_estimated_position, x.latest_estimated_position)
        ]

        if satisfying_targets:
            best = min(
                satisfying_targets,
                key=lambda x: Position.distance(
                    target.latest_estimated_position, x.latest_estimated_position
                ),
            )
            targets_set.remove(best)
        else:
            best = None

        return TimestampedPosition(
            target.latest_update_timestamp,
            Position.mean(target.latest_estimated_position, best.latest_estimated_position)
            if best is not None
            else target.latest_estimated_position,
        )

    def group_targets(self, targets: List[InTrackedTarget]) -> List[TimestampedPosition]:
        """
        Converts the provided target list to a list of timestamped center estimates.

        Iteratively computes a center estimate for each unpaired target remaining in the passed
        targets list. Targets are greedily paired with satisfying unpaired targets at each step. If
        a satisfactory pairing is found, the mean of the pair is appended to the returned list and
        both targets are no longer considered in future pairings. If no satisfactory pairing exists
        for a target, only the target's position is appended to the returned list.

        Args:
            targets: a list of observed targets.
        """
        targets_set: MutableSet[InTrackedTarget] = set(targets)
        center_estimates: List[TimestampedPosition] = []

        for target in targets:
            if target in targets_set:
                targets_set.remove(target)
                center_estimates.append(self._retrieve_center_estimate(target, targets_set))

        return center_estimates
