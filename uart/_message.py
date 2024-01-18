from abc import ABC, abstractmethod


class Message(ABC):
    """
    Base class for messages.

    Subclasses are to define _type as some 2-byte integer and add fields to store relevant message
    data.
    """

    @staticmethod
    @abstractmethod
    def get_type_id() -> int:
        """
        The type, or "message ID", of this message when sent over UART.
        """
        raise NotImplementedError()


class SerializableMessage(Message):
    """
    Base class for messages with a defined encoding scheme.

    Subclasses are to override serialize method with encoding scheme.
    """

    @abstractmethod
    def serialize(self) -> bytes:
        """
        Generates data string using message fields based on some protocol.

        Returns:
            Relevant information encoded in byte string format.
        """
        return bytes()


class ReadableMessage(Message):
    """
    Base class for messages with a defined decoding scheme.

    Subclasses are to override parse method with decoding scheme.
    """

    @classmethod
    @abstractmethod
    def parse(cls, data: bytes) -> "ReadableMessage":
        """
        Decodes data and creates appropriate class instance based on some protocol.

        Args:
            data: Relevant information encoded in byte string format.
        Returns:
            Class instance with relevant information from byte string. Subclasses are to override
            type hint with the specific subclass.
        """
        return cls()
