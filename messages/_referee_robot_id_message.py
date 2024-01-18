"""Referee Robot ID Message."""
import struct
from dataclasses import dataclass

from project_otto.uart import ReadableMessage


@dataclass
class RefereeRobotIDMessage(ReadableMessage):
    """
    Message that contains our robot's ID from the referee system.

    MCB receives this data at 10Hz from referee,
    but MCB only sends a message to Jetson when there is a change detected in the value.

    Args:
        robot_id: int representing the robot ID.
    """

    robot_id: int

    @staticmethod
    def get_type_id():
        """
        Returns this message's type ID, 0x0006.
        """
        return 0x0006

    @classmethod
    def parse(cls, data: bytes) -> "RefereeRobotIDMessage":
        """
        Method that parses a byte message and returns the results in a message dataclass.
        """
        packet_format: str = "<B"
        expected_size: int = struct.calcsize(packet_format)

        if len(data) != expected_size:
            raise ValueError(
                f"length of data must be {str(expected_size)}, received {str(len(data))}"
            )

        (robot_id,) = struct.unpack(packet_format, data)

        return RefereeRobotIDMessage(robot_id)
