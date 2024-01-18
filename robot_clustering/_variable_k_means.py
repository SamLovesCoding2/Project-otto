from typing import List, MutableSet

from project_otto.filters import LowPassFilter
from project_otto.frames import WorldFrame
from project_otto.spatial import Position
from project_otto.time import Duration
from project_otto.timestamps import JetsonTimestamp

from ._timestamped_position import TimestampedPosition

FilterType = LowPassFilter[Position[WorldFrame], JetsonTimestamp]


class VariableKMeans:
    """
    Represents a varying number of tracked centers in a three-dimensional space as moving averages.

    Each tracked center is represented as a moving average which is updated on each call to the
    update method. New center estimates are assigned to existing moving averages greedily. The
    cardinality of the set of tracked centers grows on calls to the update method for which there
    exist new center estimates that cannot be assigned to an existing tracked center moving average.
    The cardinality of the set of tracked centers decreases when the age of any of the tracked
    center moving average exceeds the specified age_limit following a call to update. The centers
    estimated by each moving average can be queried by way of the centers method.

    Args:
        age_limit: specifies the age at which moving averages are culled.
        interpolation_coefficient: the low pass filter interpolation coefficient to use in updating
        each tracked center estimate.
        max_radius: specifies the maximum radius for which a new center estimate can be
            associated with an existing tracked center.
    """

    _age_limit: Duration
    _interpolation_coefficient: float
    _max_radius: float
    _tracked_centers: List[FilterType]

    def __init__(self, age_limit: Duration, interpolation_coefficient: float, max_radius: float):
        self._age_limit = age_limit
        self._interpolation_coefficient = interpolation_coefficient
        self._max_radius = max_radius
        self._tracked_centers = []

    @property
    def num_tracked_centers(self):
        """
        Returns: the cardinality of the set of currently tracked centers.
        """
        return len(self._tracked_centers)

    @property
    def centers(self) -> List[Position[WorldFrame]]:
        """
        Returns: the current tracked center estimates.
        """
        return [x.value for x in self._tracked_centers]

    def update(self, observed_targets: List[TimestampedPosition], current_time: JetsonTimestamp):
        """
        Updates the tracked centers using the provided new center estimates.

        Each center estimate is assigned greedily to one of the tracked centers provided there
        exists an unassigned tracked center within _max_radius of the given new center estimate.
        New tracked centers moving averages are created for unassigned new center estimates and
        unassigned tracked center moving averages. Finally, tracked center moving averages greater
        older than age limit are culled.

        Args:
            observed_target: a list of timestamped center estimates.
            current_time: the current time.
        """
        new_centers: List[FilterType] = []
        available_centers: MutableSet[FilterType] = set(self._tracked_centers)

        for target in observed_targets:

            best_center = min(
                available_centers,
                default=None,
                key=lambda x: Position.distance(x.value, target.position),
            )

            if (
                best_center is None
                or Position.distance(best_center.value, target.position) > self._max_radius
            ):
                filter = LowPassFilter(
                    target.position,
                    target.timestamp,
                    self._interpolation_coefficient,
                    Position[WorldFrame].interpolate,
                )
                new_centers.append(filter)
            else:
                available_centers.remove(best_center)
                best_center.update(target.position, target.timestamp)

        self._tracked_centers = [
            x
            for x in self._tracked_centers
            if (current_time - x.latest_update_timestamp) < self._age_limit
        ] + new_centers
