from typing import Dict, Generic, List, TypeVar

from project_otto.spatial import Position
from project_otto.target_tracker import TrackedTarget
from project_otto.timestamps import JetsonTimestamp

from ._beyblade_indicator import BeybladeIndicator
from ._config import BeybladeIdentifierConfiguration

InTrackedTarget = TypeVar("InTrackedTarget", bound="TrackedTarget")


class BeybladeIdentifier(Generic[InTrackedTarget]):
    """
    Represents the beyblade identifier state.

    Beyblade identifiers maintain a map from robots' unique instance_ids their corresponding
    beyblade indicators. At each time step, the update method is intended to be called with
    two lists corresponding to robot tracked targets and plate tracked targets. Each plate is
    associated with a robot iff the distance in 3d space between the plate and robot is below
    the max_radius in the provided BeybladeIdentifierConfiguration.

    Args:
        config: the configuration for the beyblade identifier.
    """

    _config: BeybladeIdentifierConfiguration
    _tracked_robots: Dict[int, BeybladeIndicator[JetsonTimestamp]]

    def __init__(self, config: BeybladeIdentifierConfiguration):
        self._config = config
        self._tracked_robots = {}

    def _construct_indicator(
        self, time_step: JetsonTimestamp
    ) -> BeybladeIndicator[JetsonTimestamp]:
        return BeybladeIndicator(
            self._config.indicator_threshold,
            time_step,
            self._config.enter_interpolation_coefficient,
            self._config.exit_interpolation_coefficient,
        )

    def update(self, robots: List[InTrackedTarget], plates: List[InTrackedTarget]):
        """
        Updates the identifier state based on new robot and plate detections.

        Args:
            robots: list of tracked targets corresponding to robots.
            plates: list of tracked targets corresponding to plates.
        """
        self._tracked_robots = {
            robot.instance_id: self._construct_indicator(robot.latest_update_timestamp)
            if robot.instance_id not in self._tracked_robots
            else self._tracked_robots[robot.instance_id]
            for robot in robots
        }

        robot_to_relative_velocity: Dict[int, List[float]] = {
            id: [] for id in self._tracked_robots.keys()
        }

        for plate in plates:
            robot = min(
                robots,
                key=lambda x: Position.distance(
                    plate.latest_estimated_position, x.latest_estimated_position
                ),
                default=None,
            )
            if (
                robot is not None
                and Position.distance(
                    robot.latest_estimated_position, plate.latest_estimated_position
                )
                <= self._config.max_radius
            ):
                relative_velocity = (
                    robot.latest_estimated_velocity - plate.latest_estimated_velocity
                )

                robot_to_relative_velocity[robot.instance_id].append(relative_velocity.magnitude())

        for robot in robots:
            velocities = robot_to_relative_velocity[robot.instance_id]
            indicator = (
                len(velocities) > 0
                and (sum(velocities) / len(velocities))
                >= self._config.relative_velocity_magnitude_threshold
            )

            self._tracked_robots[robot.instance_id].update(indicator, robot.latest_update_timestamp)

    def is_robot_beyblading(self, robot: InTrackedTarget) -> bool:
        """
        Returns a boolean corresponding to whether the robot has been identified as beyblading.

        Args:
            robot: the robot to check for beyblading behavior
        Returns: true iff the robot is tracked and is exhibiting beyblading behavior.
        """
        return (
            robot.instance_id in self._tracked_robots
            and self._tracked_robots[robot.instance_id].value
        )
