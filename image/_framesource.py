import abc
from dataclasses import dataclass
from typing import Any, Generic, TypeVar

from project_otto.frames import Frame
from project_otto.image._frameset import Frameset
from project_otto.time import Timestamp

InFrame = TypeVar("InFrame", bound="Frame", covariant=True)
TimeType = TypeVar("TimeType", bound="Timestamp[Any]")


@dataclass
class FrameSource(Generic[InFrame, TimeType], metaclass=abc.ABCMeta):
    r"""
    A source which can capture color and depth :py:class:`Frameset`\ s upon request.

    Args:
        None
    """

    @abc.abstractmethod
    def wait_for_frames(self) -> Frameset[InFrame, TimeType]:
        """
        This method will block until a frameset is available, returning it.
        """
        pass
