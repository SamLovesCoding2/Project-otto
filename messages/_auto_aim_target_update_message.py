import struct
from dataclasses import dataclass

from project_otto.frames import WorldFrame
from project_otto.spatial import Position, Vector
from project_otto.timestamps import OdometryTimestamp
from project_otto.uart import SerializableMessage


@dataclass
class AutoAimTargetUpdateMessage(SerializableMessage):
    """
    Class for sending auto aim target updates to MCB.

    Args:
        position: Position object describing the position of the auto aim target
        velocity: Vector object describing the current velocity of the auto aim target
        acceleration: Vector object describing the current acceleration of the auto aim target
        has_target: bool that is True if there is a valid target to aim at, False otherwise
        mcb_timestamp: OdometryTimestamp object describing the MCB timestamp at which this
        target data was calculated.
    """

    position: Position[WorldFrame]
    velocity: Vector[WorldFrame]
    acceleration: Vector[WorldFrame]
    has_target: bool
    mcb_timestamp: OdometryTimestamp

    @classmethod
    def without_target(cls, mcb_timestamp: OdometryTimestamp) -> "AutoAimTargetUpdateMessage":
        """
        Creates a new AutoAimTargetUpdateMessage with no target present.

        Args:
            mcb_timestamp: the timestamp of the odometry used to compute this result
        """
        return cls(
            Position[WorldFrame](0, 0, 0),
            Vector[WorldFrame](0, 0, 0),
            Vector[WorldFrame](0, 0, 0),
            False,
            mcb_timestamp,
        )

    @classmethod
    def with_target(
        cls,
        position: Position[WorldFrame],
        velocity: Vector[WorldFrame],
        acceleration: Vector[WorldFrame],
        mcb_timestamp: OdometryTimestamp,
    ) -> "AutoAimTargetUpdateMessage":
        """
        Creates a new AutoAimTargetUpdateMessage communicating a selected target's estmated state.

        Args:
            position: the target's position
            velocity: the target's velocity
            acceleration: the target's acceleration
            mcb_timestamp: the timestamp of the odometry used to compute this result
        """
        return cls(
            position,
            velocity,
            acceleration,
            True,
            mcb_timestamp,
        )

    @staticmethod
    def get_type_id():
        """
        Returns this message's type ID, 0x0002.
        """
        return 0x0002

    def serialize(self) -> bytes:
        """
        Encodes auto aim target update data into a byte string.

        Returns:
            bytes: (positionX, positionY, positionZ,
            velocityX, velocityY, velocityZ,
            accelerationX, accelerationY, accelerationZ,
            has_target,
            mcb_timestamp)

            The data format is:
            (9x float (4 bytes each), boolean (1 byte), unsigned int (4 bytes))
        """
        return struct.pack(
            "<9f?I",
            *self.position.as_tuple(),
            *self.velocity.as_tuple(),
            *self.acceleration.as_tuple(),
            self.has_target,
            self.mcb_timestamp.time_microsecs
        )
