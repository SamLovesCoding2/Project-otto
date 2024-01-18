from typing import Callable, Generic, List, Optional, TypeVar

from project_otto.frames import WorldFrame
from project_otto.spatial import MeasuredPosition, Position
from project_otto.target_detector import DetectedTargetPosition, WorldDetectedTargetSet
from project_otto.target_tracker._config import TargetConfiguration, TrackerConfiguration
from project_otto.target_tracker._tracked_target import TrackedTarget
from project_otto.timestamps import JetsonTimestamp

InTrackedTarget = TypeVar("InTrackedTarget", bound="TrackedTarget")


class TargetTracker(Generic[InTrackedTarget]):
    """
    Class that contains all currently tracked targets.

    Args:
        config: The config instance.
        target_config: Config instance for spawned TrackedTarget instances.
        target_type: The subclass of TrackedTarget for class to contain.
    """

    def __init__(
        self,
        config: TrackerConfiguration,
        target_config: TargetConfiguration,
        target_type: Callable[
            [TargetConfiguration, MeasuredPosition[WorldFrame], JetsonTimestamp, int],
            InTrackedTarget,
        ],
    ):
        self._config = config
        self._target_config = target_config
        self._targets: List[InTrackedTarget] = []

        self._target_type = target_type

        self._next_instance_id = 1

    @property
    def all_tracked_targets(self) -> List[InTrackedTarget]:
        """
        Returns list of actively tracked targets.
        """
        return self._targets

    def update(self, measured_targets: WorldDetectedTargetSet):
        """
        Correlates and updates list of TrackedTarget using new set of measurements.

        Associates old targets with new measurements using nearest position, then updates
        associated targets with their respective measurements. Remaining targets are either
        updated via extrapolation or deleted if they haven't been correlated with any measurements
        for too long a duration. Remaining measurements are converted into new targets.

        Args:
            measured_targets: The measured target set.
        """
        new_targets: List[InTrackedTarget] = []
        measured_targets_list = list(measured_targets.positions)

        # Naive search for nearest measurement to each target
        for target in self._targets:
            extrapolated_position = target.extrapolate_position(measured_targets.jetson_timestamp)
            nearest_measurement: Optional[DetectedTargetPosition[WorldFrame]] = None
            nearest_distance = self._config.max_distance
            for measured_target in measured_targets_list:
                distance = Position.distance(
                    extrapolated_position, measured_target.measurement.position
                )
                if distance < nearest_distance:
                    nearest_measurement = measured_target
                    nearest_distance = distance

            if nearest_measurement is not None:
                target.update_from_new_position_measurement(
                    nearest_measurement.measurement, measured_targets.jetson_timestamp
                )
                new_targets.append(target)
                measured_targets_list.remove(nearest_measurement)

            elif (
                measured_targets.jetson_timestamp - target.latest_observed_timestamp
            ) <= self._config.max_staleness:
                target.update_from_extrapolation(measured_targets.jetson_timestamp)
                new_targets.append(target)

        for measured_target in measured_targets_list:
            new_targets.append(
                self._target_type(
                    self._target_config,
                    measured_target.measurement,
                    measured_targets.jetson_timestamp,
                    self._next_instance_id,
                )
            )
            self._next_instance_id += 1

        self._targets = new_targets
