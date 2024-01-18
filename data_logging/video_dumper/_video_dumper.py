import abc
import os
from abc import abstractmethod
from typing import Any, Generic, List, Optional, Tuple, TypeVar

import numpy as np
import numpy.typing as npt

from project_otto.image import Frameset
from project_otto.spatial import Frame
from project_otto.time import Timestamp

from ._video_dumper_configuration import VideoDumperConfiguration

FramesetType = TypeVar(
    "FramesetType",
    bound="Frameset[Frame, Timestamp[Any]]",
)


class VideoDumper(Generic[FramesetType], metaclass=abc.ABCMeta):
    """
    Saves a stream of frames to a given directory as chunks of video.

    A VideoDumper saves both RGB and depth data for a stream of frames into segmented video chunks
    using a given number of frames per chunk and save directory.

    Args:
        save_dir: the path to the directory in which this session's video is to be stored
        config: configuration settings for the video dumper
    """

    # Buffer frames = FPS x video chunk length (seconds)
    _config: VideoDumperConfiguration
    _dims: Optional[Tuple[int, int]]
    _save_dir: str
    _frame_list: List[FramesetType]
    _video_index: int

    def __init__(self, save_dir: str, config: VideoDumperConfiguration):
        self._config = config
        self._save_dir = save_dir
        self._frame_list = []
        self._video_index = 1
        self._dims = None

    def add_frame(self, frame_set: FramesetType):
        """
        Adds a new frame and saves a new video chunk if the queue is full.

        Args:
            frame_set: array of pixels as a frame
        """
        width = self._config.minimum_index_digits
        dims: Tuple[int, int] = (frame_set.color.shape[1], frame_set.color.shape[0])
        if self._dims is None:
            self._dims = dims
        elif self._dims != dims:
            raise ValueError(f"Expected image dimension to be {self._dims}, but got {dims}")

        self._frame_list.append(frame_set)

        if len(self._frame_list) >= self._config.num_frames_per_video_chunk:
            color_video_path = os.path.join(
                self._save_dir, f"{self._video_index:0{width}}_color.avi"
            )
            depth_video_path = os.path.join(
                self._save_dir, f"{self._video_index:0{width}}_depth.avi"
            )

            color_frames: List[npt.NDArray[np.uint8]] = list(
                map(lambda frameset: frameset.color, self._frame_list)
            )

            self._dispatch_save_chunk_job(
                depth_video_path,
                color_video_path,
                color_frames,
                [],
                self._dims,
                self._config.frame_rate,
            )
            self._video_index += 1
            self._frame_list = []

    @abstractmethod
    def _dispatch_save_chunk_job(
        self,
        depth_video_path: str,
        color_video_path: str,
        color_frames: List[npt.NDArray[np.uint8]],
        depth_frames: List[npt.NDArray[np.uint16]],
        dims: Tuple[int, int],
        frame_rate: int,
    ):
        """
        Saves the frames into a video chunk.
        """
        pass


# TODO: kill threads?
