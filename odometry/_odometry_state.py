"""Odometry data type."""
from dataclasses import dataclass

from project_otto.frames import (
    TurretBaseReferencePointFrame,
    TurretYawReferencePointFrame,
    WorldFrame,
)
from project_otto.spatial import Orientation, Position
from project_otto.timestamps import OdometryTimestamp


@dataclass
class OdometryState:
    """
    Data structure used to hold information for odometry.

    Contains the raw data of a single Transform from World to Turret.
    This includes the position and orientation.
    Also contains the associated MCB :class:`~project_otto.time.Timestamp`.
    """

    position: Position[WorldFrame]
    pitch: Orientation[TurretYawReferencePointFrame]
    yaw: Orientation[TurretBaseReferencePointFrame]
    timestamp: OdometryTimestamp
