"""
Configurations used in Project Otto.
"""
from dataclasses import dataclass

from project_otto.beyblade_identification import BeybladeIdentifierConfiguration
from project_otto.data_logging import LogDirectorySelectorConfig, VideoDumperConfiguration
from project_otto.frames import (
    ColorCameraFrame,
    LauncherFrame,
    TurretReferencePointFrame,
    TurretYawReferencePointFrame,
)
from project_otto.robot_clustering import RobotClustererConfiguration
from project_otto.spatial import Position, Transform
from project_otto.target_detector import (
    DetectorConfiguration,
    TargetProjectionUncertaintyConfig,
    TargetPruneConfiguration,
)
from project_otto.target_selection import TargetSelectorConfiguration
from project_otto.target_tracker import TargetConfiguration, TrackerConfiguration
from project_otto.time import Duration, TimestampedHistoryBufferConfiguration
from project_otto.uart import (
    PerseveringReceiverConfiguration,
    SerialConfiguration,
    TransceiverConfiguration,
)
from project_otto.webserver import ServerConfiguration


@dataclass
class RealSenseResetConfiguration:
    """
    Options specifying what devices to remove, and what approaches to apply.
    """

    reset_usb: bool = True
    reset_hardware: bool = True
    vendor_id: int = 0x8086
    product_id: int = 0x0B07


@dataclass
class CoreConfiguration:
    """
    Configuration for the overall system and main loop, not specific to any one subsystem.
    """

    fps_log_interval: Duration = Duration.from_seconds(20)
    fps_log_low_fps_threshold: float = 30


@dataclass
class McbCommsConfiguration(TransceiverConfiguration, SerialConfiguration):
    """
    Options for MCB comms, covering the serial link and transceiver.

    Merges both parent classes into one option.
    """

    pass


@dataclass
class RobotIdentityConfiguration:
    """
    Options specifying which robot we are and how it is mechanically structured.
    """

    turret_reference_to_camera_transform: Transform[TurretReferencePointFrame, ColorCameraFrame]
    turret_reference_to_launcher_transform: Transform[TurretReferencePointFrame, LauncherFrame]
    yaw_reference_to_pitch_reference_transform: Position[TurretYawReferencePointFrame]


@dataclass
class RobotUncertaintyConfig:
    """
    Options controlling uncertainty in robot state estimation.
    """

    robot_position_variance: float


@dataclass
class ApplicationConfiguration:
    """
    Top-level configuration for the system. Contains other configs as children.

    Args:
        logging: Global log output settings
        video_dumper: Options to control the saving of video footage to disk
        mcb_comms: Configuration for a UART serial link communicating with the host processor (MCB)
        core: miscellaneous options for the main app loop
        server: Options for the networked debug server
        odometry_buffer:
            Configuration for the :class:`TimestampedHistoryBuffer` used to store odometry.

            Entries must exist in the buffer long enough for any frame captured by the RealSense
            around that point in time to have made it to the Jetson and begun processing.
        detector: configuration for the target detector
        plate_filtering: Rules for eagerly eliminating low-quality detections
        plate_projection_uncertainty: Controls the uncertainty assigned to detected plates
        robot_uncertainty: Options controlling the variance of tracked robots
        tracker: configuration for the target tracker
        target_estimation: configuration for target motion estimation
    """

    # Meta:
    logging: LogDirectorySelectorConfig
    video_dumper: VideoDumperConfiguration
    mcb_comms: McbCommsConfiguration
    identity: RobotIdentityConfiguration
    persevering_receiver: PerseveringReceiverConfiguration
    core: CoreConfiguration
    server: ServerConfiguration

    # "frontend"
    realsense_reset: RealSenseResetConfiguration
    odometry_buffer: TimestampedHistoryBufferConfiguration
    detector: DetectorConfiguration
    plate_filtering: TargetPruneConfiguration
    plate_projection_uncertainty: TargetProjectionUncertaintyConfig
    robot_uncertainty: RobotUncertaintyConfig

    # "backend"
    tracker: TrackerConfiguration
    target_estimation: TargetConfiguration
    target_selector: TargetSelectorConfiguration
    robot_clusterer: RobotClustererConfiguration
    beyblade_identifier: BeybladeIdentifierConfiguration
