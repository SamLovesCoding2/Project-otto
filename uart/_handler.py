from abc import ABC, abstractmethod
from typing import Any, Generic, Type, TypeVar

from project_otto.time import Timestamp

from ._message import ReadableMessage

InReadableMessage = TypeVar("InReadableMessage", bound="ReadableMessage")
TimestampType = TypeVar("TimestampType", bound="Timestamp[Any]")


class RxHandler(ABC, Generic[InReadableMessage, TimestampType]):
    """
    Base class for message handlers.

    Subclasses to define _msg_cls, replace the TypeVar argument, and override handle method to
    define what to do upon receiving a message.
    """

    _msg_cls: Type[InReadableMessage]

    @property
    def type_id(self) -> int:
        """
        Returns the type, or "message ID", of the message this handler can receive.
        """
        return self._msg_cls.get_type_id()

    @property
    def msg_class(self) -> Type[InReadableMessage]:
        """
        Returns the ReadableMessage subclass that this handler class is associated with.
        """
        return self._msg_cls

    @abstractmethod
    def handle(self, msg: InReadableMessage, timestamp: TimestampType):
        """
        What the handler does based on the message received.

        Args:
            msg: The message received. Subclasses are to override type hint with the appropriate
                ReadableMessage subclass.
        """
        pass
