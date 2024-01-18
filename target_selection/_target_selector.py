from typing import Generic, Optional, TypeVar

from project_otto.beyblade_identification import BeybladeIdentifier
from project_otto.spatial import Position
from project_otto.target_tracker import TrackedTarget

from ._target_selector_update_state import TargetSelectorUpdateState

InTrackedTarget = TypeVar("InTrackedTarget", bound=TrackedTarget)


class TargetSelector(Generic[InTrackedTarget]):
    """
    Selects targets using a robot-centric policy.

    Robot targets remain selected until either the robot target is no longer available or the
    selected robot is manually changed by way of calling the reselect method. If the selected robot
    is beyblading then the robot is targeted. Otherwise, the optimal plate in the latest plate
    sequence within the provided maximum radius of the selected robot is targeted.

    Args:
        identifier: the identifier to use for beyblade identification.
        max_radius: the maximum radius for which a plate is associated with a selected robot.
    """

    _robot_target: Optional[InTrackedTarget]
    _plate_target: Optional[InTrackedTarget]
    _last_update_state: TargetSelectorUpdateState[InTrackedTarget]
    _identifier: BeybladeIdentifier[InTrackedTarget]
    _max_radius: float

    def __init__(
        self,
        identifier: BeybladeIdentifier[InTrackedTarget],
        max_radius: float,
    ):
        self._robot_target = None
        self._plate_target = None
        self._last_update_state = TargetSelectorUpdateState(lambda _: None, lambda _: None, [], [])
        self._identifier = identifier
        self._max_radius = max_radius

    def _reselect_robot(self, update_state: TargetSelectorUpdateState[InTrackedTarget]):
        self._robot_target = update_state.robot_selector(update_state.robots)

    def _reselect_plate(self, update_state: TargetSelectorUpdateState[InTrackedTarget]):
        if self._robot_target is not None:
            robot_position = self._robot_target.latest_estimated_position
            filtered_plates = [
                plate
                for plate in update_state.plates
                if Position.distance(robot_position, plate.latest_estimated_position)
                < self._max_radius
            ]
            self._plate_target = update_state.plate_selector(filtered_plates)
        else:
            self._plate_target = None

    @property
    def robot_target(self) -> Optional[InTrackedTarget]:
        """
        Returns the selected robot target.
        """
        return self._robot_target

    @property
    def plate_target(self) -> Optional[InTrackedTarget]:
        """
        Returns the selected plate target.
        """
        return self._plate_target

    @property
    def target(self) -> Optional[InTrackedTarget]:
        """
        Returns the (hopefully) optimal target.
        """
        if self._robot_target is None or self._identifier.is_robot_beyblading(self._robot_target):
            return self._robot_target
        else:
            return self._plate_target

    def update(self, update_state: TargetSelectorUpdateState[InTrackedTarget]):
        """
        Updates the target selector based on the provided update_state.

        Args:
            update_state: The state to use to update the target selector.
        """
        self._identifier.update(update_state.robots, update_state.plates)
        self._last_update_state = update_state

        if self._robot_target is None or self._robot_target not in update_state.robots:
            self._reselect_robot(update_state)
        self._reselect_plate(update_state)

    def reselect(self):
        """
        Reselects a robot target using the latest provided update state.
        """
        self._reselect_robot(self._last_update_state)
        self._reselect_plate(self._last_update_state)
