import logging
from typing import Optional, Sequence, Tuple, TypeVar

from project_otto.target_tracker import TrackedTarget

from ._config import TargetSelectorConfiguration
from ._target_selection_rules import TargetSelectionRule

TargetType = TypeVar("TargetType", bound="TrackedTarget")


def select_target(
    config: TargetSelectorConfiguration,
    rules: Sequence[Tuple[TargetSelectionRule, float]],
    targets: Sequence[TargetType],
) -> Optional[TargetType]:
    """
    Finds the best target from a list of targets.

    The best target has the lowest weighted sum of scores for the target selection rules
    specified by the configuration. Returns None if none of the given targets are valid.

    Args:
        config: basic configuration parameters to influence the selection algorithm
        rules: A list of scoring rules and their relative weights.
        targets: List of targets to evaluate
    Returns:
        The target with the lowest evaluation score, None if no target is valid.
    """
    target_scores = list(map(lambda target: (target, _evaluate_target(rules, target)), targets))

    def _is_under_maximum_score(score: float):
        return config.maximum_score_threshold is None or score < config.maximum_score_threshold

    valid_targets = [
        (target, score)
        for target, score in target_scores
        if score is not None and _is_under_maximum_score(score)
    ]

    if len(valid_targets) == 0:
        return None

    min_target, _ = min(valid_targets, key=lambda target_score: target_score[1])
    return min_target


def _evaluate_target(
    rules: Sequence[Tuple[TargetSelectionRule, float]], target: TrackedTarget
) -> Optional[float]:
    """
    Evaluates the score and validity of a given target, lower scores being preferable.

    Calculates the weighted sum of scores for the given target using rules from the config.
    If the target is marked as invalid by any of the rules, then it is invalid.

    Args:
        rules: A list of scoring rules and their relative weights.
        target: Target to evaluate

    Returns:
        Weighted sum of scores using the rules and weights from the config, or None
        if the target is invalid.
    """
    weighted_score = 0
    for rule, weight in rules:
        rule_score = rule.get_score(target)
        if rule_score is None:
            logging.info("Dropped invalid target")
            return None
        weighted_score += weight * rule_score
    return weighted_score
