"""Shutdown message."""
from dataclasses import dataclass

from project_otto.uart import ReadableMessage


@dataclass
class ShutdownMessage(ReadableMessage):
    """
    Message that tells the robot to shutdown.
    """

    @staticmethod
    def get_type_id():
        """
        Returns this message's type ID, 0x0009.
        """
        return 0x0009

    @classmethod
    def parse(cls, data: bytes) -> "ShutdownMessage":
        """
        Method that parses a byte message and returns the results in a message dataclass.

        Note that there is no byte message for this message.
        """
        return ShutdownMessage()
