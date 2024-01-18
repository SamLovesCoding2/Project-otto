"""Referee Warning Message."""
import struct
from dataclasses import dataclass

from project_otto.uart import ReadableMessage


@dataclass
class RefereeWarningMessage(ReadableMessage):
    """
    Message that contains warning message data from the referee system.

    Sent when our team receives a warning from the referee system.

    Args:
        warning_level: int representing the warning level.
        foul_robot_id: int representing the foul robot ID.
    """

    warning_level: int
    foul_robot_id: int

    @staticmethod
    def get_type_id():
        """
        Returns this message's type ID, 0x0005.
        """
        return 0x0005

    @classmethod
    def parse(cls, data: bytes) -> "RefereeWarningMessage":
        """
        Method that parses a byte message and returns the results in a message dataclass.
        """
        packet_format: str = "<2B"
        expected_size: int = struct.calcsize(packet_format)

        if len(data) != expected_size:
            raise ValueError(
                f"length of data must be {str(expected_size)}, received {str(len(data))}"
            )

        (warning_level, foul_robot_id) = struct.unpack(packet_format, data)

        return RefereeWarningMessage(warning_level, foul_robot_id)
