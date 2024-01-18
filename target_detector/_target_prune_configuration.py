"""Init for Classifies Target."""
from dataclasses import dataclass


@dataclass
class TargetPruneConfiguration:
    """
    Represents a const value for breadth and length, basis to compare against for filtering targets.
    """

    minimum_width: int
    minimum_height: int
