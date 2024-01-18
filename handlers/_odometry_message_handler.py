import logging
import math

from project_otto.frames import (
    TurretBaseReferencePointFrame,
    TurretYawReferencePointFrame,
    WorldFrame,
)
from project_otto.messages import OdometryMessage
from project_otto.odometry import OdometryState
from project_otto.spatial import Orientation, Position
from project_otto.time import BufferEntryTooOldError, Duration, TimestampedHistoryBuffer
from project_otto.timestamps import JetsonTimestamp, OdometryTimestamp
from project_otto.uart import RxHandler

# TODO: https://gitlab.com/aruw/vision/project-otto/-/issues/205
ODOMETRY_MANUAL_TIME_OFFSET_USECS = 9_000


class OdometryMessageHandler(RxHandler[OdometryMessage, JetsonTimestamp]):
    """
    Handler for OdometryMessage.

    Args:
        odometry_buffer:
            a :class:`TimestampedHistoryBuffer[JetsonTimestamp, OdometryState]`
            into which received :class:`OdometryState` objects should be put.
    """

    _msg_cls = OdometryMessage

    def __init__(self, odometry_buffer: TimestampedHistoryBuffer[JetsonTimestamp, OdometryState]):
        self._odometry_buffer = odometry_buffer

    def handle(self, msg: OdometryMessage, timestamp: JetsonTimestamp):
        """
        Handle an OdometryMessage.

        Load the data from the given OdometryMessage into a OdometryState object,
        then add that object into the odometry TimestampedHistoryBuffer.

        Args:
            msg: an :class:`OdometryMessage`.
            timestamp: an :class:`JetsonTimestamp` that represents the time
            that this message was received.
        """
        chassis_position = Position[WorldFrame](msg.x_pos, msg.y_pos, msg.z_pos)

        turret = msg.turrets[0]
        turret_pitch = Orientation[TurretYawReferencePointFrame].from_euler_angles(
            0, math.radians(turret[1]), 0
        )
        turret_yaw = Orientation[TurretBaseReferencePointFrame].from_euler_angles(
            0,
            0,
            math.radians(turret[2]),
        )
        turret_timestamp = OdometryTimestamp(turret[0])
        turret_odometry_state = OdometryState(
            chassis_position, turret_pitch, turret_yaw, turret_timestamp
        )

        local_timestamp = timestamp - Duration(ODOMETRY_MANUAL_TIME_OFFSET_USECS)
        try:
            self._odometry_buffer.add(local_timestamp, turret_odometry_state)
        except BufferEntryTooOldError as e:
            e: BufferEntryTooOldError[JetsonTimestamp]
            logging.warning(f"Failed to register new odometry data: {e}")
