import abc

from ._message import SerializableMessage


class HostMessageTransmitter(metaclass=abc.ABCMeta):
    """
    An interface for transmitters.

    """

    @abc.abstractmethod
    def send(self, msg: "SerializableMessage", seq_num: int = 0):
        """
        Transmits a message to the MCB.
        """
        pass
