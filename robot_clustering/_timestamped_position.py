from dataclasses import dataclass

from project_otto.frames import WorldFrame
from project_otto.spatial import Position
from project_otto.timestamps import JetsonTimestamp


@dataclass(frozen=True)
class TimestampedPosition:
    """
    Represents a timestamp, position pair.
    """

    timestamp: JetsonTimestamp
    position: Position[WorldFrame]
