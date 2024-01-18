from abc import ABC, abstractmethod
from typing import Any

from project_otto.time import Timestamp
from project_otto.uart import Message


class MessageStore(ABC):
    """
    Interface for a persistent log of host messages received in a session.

    Intended to be used to record the inputs to our system and later replay it on a different
    device.
    """

    @abstractmethod
    def store_message(self, message: Message, receipt_time: Timestamp[Any]):
        """
        Store the given Message to the backing store.

        Arg:
            message: The Message to be stored.
            receipt_time: The time at which this message was received.
        """
        pass
