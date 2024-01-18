"""New Target Message."""
import struct
from dataclasses import dataclass

from project_otto.uart import ReadableMessage


@dataclass
class SelectNewTargetMessage(ReadableMessage):
    """
    Message that signifies a request for a new target to aim at.

    Args:
        request_id: an :int: that represents the seqeuence number of the target
    """

    @staticmethod
    def get_type_id():
        """
        Returns this message's type ID, 0x0007.
        """
        return 0x0007

    request_id: int

    @classmethod
    def parse(cls, data: bytes) -> "SelectNewTargetMessage":
        """
        Method that parses a byte message and returns the results in a message dataclass.
        """
        packet_format = "<I"
        expected_size = struct.calcsize(packet_format)

        if len(data) != expected_size:
            raise ValueError(f"length of data must be {expected_size}")

        request_id = struct.unpack(packet_format, data)[0]

        return SelectNewTargetMessage(request_id)
