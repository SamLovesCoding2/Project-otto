"""Function to filter out targets."""
import logging
from typing import Set

from project_otto.robomaster import TeamColor
from project_otto.target_detector._target import DetectedTargetRegion
from project_otto.target_detector._target_prune_configuration import TargetPruneConfiguration
from project_otto.target_detector._target_set import ImageDetectedTargetSet


def prune_invalid_targets(
    current_team_color: TeamColor,
    targets: ImageDetectedTargetSet,
    config: TargetPruneConfiguration,
) -> ImageDetectedTargetSet:
    """
    Filters targets based on rectangle size and the team color.

    Based on the set of targets provided as a parameter, the rectangles of target that are too
    small will be filtered out, and those that detect another robot's color to be the same as ours
    will be filtered out.

    Args:
        current_team_color: provide the color of our team
        targets: provide a set of targets
        config: config class for this method

    Returns:
        a set of targets that are of type ImageDetectedTargetSet
    """
    size_rejection_count = 0
    correct_targets: Set[DetectedTargetRegion] = set()
    for item in targets.plates:
        if current_team_color != item.color:
            length_rect = item.rectangle.height
            breadth_rect = item.rectangle.width
            if breadth_rect < config.minimum_width or length_rect < config.minimum_height:
                size_rejection_count += 1
                continue

            correct_targets.add(item)

    if size_rejection_count > 0:
        logging.info(f"Rejected {size_rejection_count} detections due to size constraint")

    return ImageDetectedTargetSet(correct_targets)
