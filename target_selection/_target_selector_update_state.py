from dataclasses import dataclass
from typing import Callable, Generic, List, Optional, Sequence, TypeVar

from project_otto.target_tracker import TrackedTarget

InTrackedTarget = TypeVar("InTrackedTarget", bound=TrackedTarget)


@dataclass
class TargetSelectorUpdateState(Generic[InTrackedTarget]):
    """
    Represents the target selector update state.

    Args:
        robot_selector: callable optionally returning the optimal robot target in a sequence of
          robot targets.
        plate_selector: callable optionally returning the optimal plate target in a sequence of
          robot targets.
        robots: a list of observed robot targets
        plates: a list of observed plate targets
    """

    robot_selector: Callable[[Sequence[InTrackedTarget]], Optional[InTrackedTarget]]
    plate_selector: Callable[[Sequence[InTrackedTarget]], Optional[InTrackedTarget]]
    robots: List[InTrackedTarget]
    plates: List[InTrackedTarget]
