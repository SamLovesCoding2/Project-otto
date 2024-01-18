"""
FrameSource definitions specific to Project Otto.
"""
import abc
import logging
import time
from dataclasses import asdict, dataclass
from typing import Any, Dict, List

import numpy as np
import numpy.typing as npt
import pyrealsense2 as rs  # type: ignore
import usb  # type: ignore

from project_otto.frames import ColorCameraFrame
from project_otto.framesets import RealsenseFrameset
from project_otto.image import FrameSource
from project_otto.timestamps import JetsonTimestamp

# https://github.com/IntelRealSense/librealsense/blob/c94410a420b74e5fb6a414bd12215c05ddd82b69/include/librealsense2/h/rs_types.h#L44
REALSENSE_LENS_MODEL_IDS: Dict[int, Any] = {
    0: rs.distortion.none,
    1: rs.distortion.modified_brown_conrady,
    2: rs.distortion.inverse_brown_conrady,
    3: rs.distortion.ftheta,
    4: rs.distortion.brown_conrady,
    5: rs.distortion.kannala_brandt4,
}


@dataclass
class RealsenseConfig:
    """
    Settings for the RealSense camera.

    Args:
        color_width: width of the color camera image, in pixels
        color_height: height of the color camera image, in pixels
        color_fps: desired frames-per-second of the color camera stream
        color_auto_exposure: boolean indicating whether auto-exposure should be enabled
        color_exposure: manual exposure setting of the color camera in underlying driver units
        color_brightness: brightness setting of the color camera in underlying driver units
        color_contrast: contrast setting of the color camera in underlying driver units
        color_gain: gain setting of the color camera in underlying driver units
        color_gamma: gamma setting of the color camera in underlying driver units
        color_saturation: saturation setting of the color camera in underlying driver units
        depth_width: width of the depth camera image, in pixels
        depth_height: height of the depth camera image, in pixels
        depth_fps: desired frames-per-second of the depth camera stream
    """

    color_width: int = 960
    color_height: int = 540
    color_fps: int = 60
    color_auto_exposure: bool = False
    color_exposure: int = 60
    color_brightness: int = 0
    color_contrast: int = 50
    color_gain: int = 128
    color_gamma: int = 500
    color_saturation: int = 64

    depth_width: int = 640
    depth_height: int = 360
    depth_fps: int = 60


def reset_usb_connection(vendor_id: int, product_id: int):
    """
    Resets the usb connection with the associated IDs.

    """
    devices = usb.core.find(idVendor=vendor_id, idProduct=product_id, find_all=True)  # type: ignore
    try:
        for dev in devices:  # type: ignore
            dev.reset()
        time.sleep(1)
    except BaseException as e:
        logging.error("Failed to reset RealSense USB connection.", exc_info=e)


def hardware_reset():
    """
    Hardware resets all connected RealSense devices.

    """
    ctx: Any = rs.context()
    devices: Any = ctx.query_devices()
    for dev in devices:
        dev.hardware_reset()
    time.sleep(1)  # superstition


@dataclass
class RealsenseIntrinsics:
    """
    Color camera lens intrinsics for the Realsense.
    """

    width: int
    height: int
    ppx: float
    ppy: float
    fx: float
    fy: float
    model: int
    coeffs: List[float]

    @classmethod
    def from_rs_intrinsics(cls, rs_intrinsics: Any) -> "RealsenseIntrinsics":
        """
        Creates a new RealsenseIntrinsics object from a realsense intrinsics object.
        """
        return RealsenseIntrinsics(
            rs_intrinsics.width,
            rs_intrinsics.height,
            rs_intrinsics.ppx,
            rs_intrinsics.ppy,
            rs_intrinsics.fx,
            rs_intrinsics.fy,
            rs_intrinsics.model.value,
            rs_intrinsics.coeffs,
        )

    def as_rs_intrinsics(self) -> Any:
        """
        Returns the corresponding realsense intrinsics object.
        """
        intrinsics: Any = rs.intrinsics()
        intrinsics.width = self.width
        intrinsics.height = self.height
        intrinsics.ppx = self.ppx
        intrinsics.ppy = self.ppy
        intrinsics.fx = self.fx
        intrinsics.fy = self.fy
        intrinsics.model = REALSENSE_LENS_MODEL_IDS[self.model]
        intrinsics.coeffs = self.coeffs

        return intrinsics

    def as_dict(self) -> Dict[str, Any]:
        """
        Returns a dict storing all of the properties of a realsense intrinsics object.
        """
        return asdict(self)

    @staticmethod
    def from_dict(intrinsics_dump: Dict[str, Any]) -> "RealsenseIntrinsics":
        """
        Returns a realsense intrinsics object from a dumped dict.
        """
        return RealsenseIntrinsics(**intrinsics_dump)


@dataclass
class RealsenseFramesetSource(
    FrameSource[ColorCameraFrame, JetsonTimestamp], metaclass=abc.ABCMeta
):
    """
    FrameSource that outputs RealsenseFramesets.
    """

    config: RealsenseConfig

    def __post_init__(self):
        """
        Setup camera feeds.
        """
        self.pipeline: Any = rs.pipeline()
        self.rs_config: Any = rs.config()
        self.rs_config.enable_stream(
            rs.stream.depth,
            self.config.depth_width,
            self.config.depth_height,
            rs.format.z16,
            self.config.depth_fps,
        )
        self.rs_config.enable_stream(
            rs.stream.color,
            self.config.color_width,
            self.config.color_height,
            rs.format.bgr8,
            self.config.color_fps,
        )

        self.profile: Any = self.pipeline.start(self.rs_config)

        color_sensor: Any = next(
            sensor for sensor in self.profile.get_device().sensors if not sensor.is_depth_sensor()
        )
        color_sensor.set_option(rs.option.enable_auto_exposure, self.config.color_auto_exposure)
        color_sensor.set_option(rs.option.exposure, self.config.color_exposure)
        color_sensor.set_option(rs.option.brightness, self.config.color_brightness)
        color_sensor.set_option(rs.option.contrast, self.config.color_contrast)
        color_sensor.set_option(rs.option.gain, self.config.color_gain)
        color_sensor.set_option(rs.option.gamma, self.config.color_gamma)
        color_sensor.set_option(rs.option.saturation, self.config.color_saturation)
        self.align: Any = rs.align(rs.stream.color)

        profile: Any = self.pipeline.get_active_profile()
        color_profile: Any = rs.video_stream_profile(profile.get_stream(rs.stream.color))
        self.color_intrinsics: Any = color_profile.get_intrinsics()

    def wait_for_frames(self) -> RealsenseFrameset:
        """
        Blocks until we get a frameset from the Realsense.
        """
        frames: Any = self.pipeline.wait_for_frames()

        aligned_frames: Any = self.align.process(frames)

        color_frame: Any = aligned_frames.get_color_frame()
        depth_frame: Any = aligned_frames.get_depth_frame()

        capture_time: int = (
            color_frame.get_frame_metadata(rs.frame_metadata_value.backend_timestamp) * 1000
        )

        color_frame_np: npt.NDArray[np.uint8] = np.array(color_frame.get_data(), dtype=np.uint8)
        depth_frame_np: npt.NDArray[np.uint16] = np.array(depth_frame.get_data(), dtype=np.uint16)

        return RealsenseFrameset(
            color_frame_np, depth_frame_np, JetsonTimestamp(capture_time), self.color_intrinsics
        )
