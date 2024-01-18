import abc
from typing import Optional


class HostMessageReceiver(metaclass=abc.ABCMeta):
    """
    An interface for receivers.

    """

    @abc.abstractmethod
    def process_in(self, max_packets: Optional[int] = None):
        """
        Processes packets send by the MCB.
        """
        pass

    @abc.abstractmethod
    def reset_states(self):
        """
        Clears the states of the receiver.
        """
        pass
