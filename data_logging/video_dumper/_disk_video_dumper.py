import logging
import time
from threading import Thread
from typing import Any, List, Tuple, TypeVar

import cv2  # type: ignore
import numpy as np
import numpy.typing as npt

from project_otto.image import Frameset
from project_otto.spatial import Frame
from project_otto.time import Timestamp

from ._video_dumper import VideoDumper
from ._video_dumper_configuration import VideoDumperConfiguration

FramesetType = TypeVar("FramesetType", bound="Frameset[Frame, Timestamp[Any]]")


class DiskVideoDumper(VideoDumper[FramesetType]):
    """
    VideoDumper that saves video chunks to disk.
    """

    def __init__(self, save_dir: str, config: VideoDumperConfiguration):
        super(DiskVideoDumper, self).__init__(save_dir, config)
        self._job_number = 0

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
        Passes parameters to a static method which saves the frames to a video in a subprocess.

        This wrapper method is necessary in order to be stubbed for unit testing.

        Args:
            video_path: path to save the video
            frame_queue: queue of frame sets to be saved to the video, in order
            dims: dimensions of the image
            frame_rate: FPS of output video
        """
        p = Thread(
            target=DiskVideoDumper._save_chunk,
            args=(depth_video_path, color_video_path, color_frames, depth_frames, dims, frame_rate),
            name=f"video_dumper_{self._job_number}",
            daemon=True,
        )
        p.start()
        self._job_number += 1

    @staticmethod
    def _save_chunk(
        depth_video_path: str,
        color_video_path: str,
        color_frames: List[npt.NDArray[np.uint8]],
        depth_frames: List[npt.NDArray[np.uint16]],
        dims: Tuple[int, int],
        frame_rate: int,
    ):
        """
        Saves given frames into a video segment at the given path and video index.

        This operation is static so that it can run in a separate process to avoid blocking
        other operations. The video index is used to create a unique file name for the new
        video segment within the save directory. Uses OpenCV VideoWriter with the XVID encoder.

        Args:
            video_path: path to save the video
            frame_queue: queue of frame sets to be saved to the video, in order
            dims: dimensions of the image
            frame_rate: FPS of output video
        """
        logging.info(f"Beginning save video chunk to: {color_video_path} and {depth_video_path}")
        # TODO: save depth
        start_time = time.time()
        color_fourcc: Any = cv2.VideoWriter_fourcc(*"XVID")
        color_writer: Any = cv2.VideoWriter(color_video_path, color_fourcc, frame_rate, dims, True)

        for color_frame in color_frames:
            color_writer.write(color_frame)

        color_writer.release()
        time_taken = time.time() - start_time
        logging.info(
            f"Finished save video chunk after {time_taken:.2f}s:"
            + f" {color_video_path} and {depth_video_path}"
        )
