from dataclasses import dataclass
from typing import Generic, TypeVar

from ._frame import Frame
from ._linear_uncertainty import LinearUncertainty
from ._position import Position

InFrame = TypeVar("InFrame", bound="Frame")


@dataclass(frozen=True)
class MeasuredPosition(Generic[InFrame]):
    """
    A Position paired with a LinearUncertainty, representing the (co)variance of the position.
    """

    position: Position[InFrame]
    uncertainty: LinearUncertainty[InFrame]
