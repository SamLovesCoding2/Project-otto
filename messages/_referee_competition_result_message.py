"""Referee Competition Result Message."""
import struct
from dataclasses import dataclass

from project_otto.uart import ReadableMessage


@dataclass
class RefereeCompetitionResultMessage(ReadableMessage):
    """
    Message that contains competition result data from the referee system.

    Sent when the competition ends.

    Args:
        competition_result: int representing the competition result.
    """

    competition_result: int

    @staticmethod
    def get_type_id():
        """
        Returns this message's type ID, 0x0004.
        """
        return 0x0004

    @classmethod
    def parse(cls, data: bytes) -> "RefereeCompetitionResultMessage":
        """
        Method that parses a byte message and returns the results in a message dataclass.
        """
        packet_format: str = "<B"
        expected_size: int = struct.calcsize(packet_format)

        if len(data) != expected_size:
            raise ValueError(
                f"length of data must be {str(expected_size)}, received {str(len(data))}"
            )

        (competition_result,) = struct.unpack(packet_format, data)

        return RefereeCompetitionResultMessage(competition_result)
