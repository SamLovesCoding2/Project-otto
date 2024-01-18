"""Data class to represent a target, with a bounding rectangle and color."""
from dataclasses import dataclass
from typing import Generic, TypeVar

from project_otto.geometry.rectangle import IntRectangle
from project_otto.robomaster import TeamColor
from project_otto.spatial import Frame, MeasuredPosition

InFrame = TypeVar("InFrame", bound="Frame")


@dataclass(frozen=True)
class DetectedTargetRegion:
    """
    Represents an individual target, such as a single plate.

    Contains the :class:`~project_otto.robomaster.TeamColor` of the target and the
    :class:`~project_otto.geometry.Rectangle` bounding it.
    """

    detection_confidence: float
    color: TeamColor
    rectangle: IntRectangle


@dataclass(frozen=True)
class DetectedTargetPosition(Generic[InFrame]):
    """
    An individual target's position in 3D space in the given frame.

    Contains the 3D position in the given frame as a :class:`~project_otto.spatial.Position`, and
    the `:class:`~project_otto.robomaster.TeamColor` of the target.
    """

    confidence: float
    color: TeamColor
    measurement: MeasuredPosition[InFrame]
