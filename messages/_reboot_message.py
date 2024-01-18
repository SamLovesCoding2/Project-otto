"""Reboot Message."""
from dataclasses import dataclass

from project_otto.uart import ReadableMessage


@dataclass
class RebootMessage(ReadableMessage):
    """
    Message that tells the robot to reboot.
    """

    @staticmethod
    def get_type_id():
        """
        Returns this message's type ID, 0x0008.
        """
        return 0x0008

    @classmethod
    def parse(cls, data: bytes) -> "RebootMessage":
        """
        Method that parses a byte message and returns the results in a message dataclass.

        Note that there is no byte message for this message.
        """
        return RebootMessage()
