"""Referee Realtime Data Message."""
import struct
from dataclasses import dataclass
from typing import Tuple

import bitstruct  # type: ignore

from project_otto.uart import ReadableMessage


@dataclass
class RefereeRealtimeDataMessage(ReadableMessage):
    """
    Message that contains realtime logging data from the referee system.

    Args:
        competition_type: int representing the current competition type.
        competition_stage: int representing the current stage of the competition.
        remaining_round_time: int containing number of seconds remaining in the match.
        update_unix_time: int with the Unix timestamp of the competition status update.
        power_gimbal: bool representing whether there is 24V output from the gimbal port.
        power_chassis: bool representing whether there is 24V output from the chassis port.
        power_shooter: bool representing whether there is 24V output from the shooter port.
    """

    competition_type: int
    competition_stage: int
    remaining_round_time: int
    update_unix_time: int
    power_gimbal: bool
    power_chassis: bool
    power_shooter: bool

    @staticmethod
    def get_type_id():
        """
        Returns this message's type ID, 0x0003.
        """
        return 0x0003

    @classmethod
    def parse(cls, data: bytes) -> "RefereeRealtimeDataMessage":
        """
        Method that parses a byte message and returns the results in a message dataclass.
        """
        packet_format: str = "<cHQc"
        expected_size: int = struct.calcsize(packet_format)

        if len(data) != expected_size:
            raise ValueError(
                f"length of data must be {str(expected_size)}, received {str(len(data))}"
            )

        competition_byte, remaining_round_time, update_unix_time, power_byte = struct.unpack(
            packet_format, data
        )

        competition_byte_tuple: Tuple[int, int] = bitstruct.unpack(">u4u4", competition_byte)
        power_byte_tuple: Tuple[bool, bool, bool] = bitstruct.unpack(">p5b1b1b1", power_byte)

        # order is reversed because bitstruct puts the value
        # from the first bit (on the right) into the last index on the tuple
        # (ex. 0b00000011 = (False, True, True))
        return RefereeRealtimeDataMessage(
            competition_byte_tuple[1],
            competition_byte_tuple[0],
            remaining_round_time,
            update_unix_time,
            power_byte_tuple[2],
            power_byte_tuple[1],
            power_byte_tuple[0],
        )
