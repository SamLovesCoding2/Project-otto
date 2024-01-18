from dataclasses import dataclass
from typing import Optional


@dataclass
class TargetSelectorConfiguration:
    """
    Configuration for how targets should be evaluated and selected.

    Args:
        maximum_score_threshold: A maximum score threshold for selecting valid targets
        max_radius: The maximum radius for which a plate is associated with a robot
    """

    maximum_score_threshold: Optional[float]
    max_radius: float
