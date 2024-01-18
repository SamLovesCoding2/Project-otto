"""
Main Loop that runs the vision process.
"""

import argparse
import http.server
import logging
import os
import time
from threading import Thread
from time import perf_counter
from types import TracebackType
from typing import Any, Callable, List, Optional, Sequence, Set, Type

import torch

from project_otto.application_config import ApplicationConfiguration
from project_otto.beyblade_identification import BeybladeIdentifier
from project_otto.config_deserialization import load_merged_yaml_from_files
from project_otto.data_logging import DiskVideoDumper, LogDirectorySelector, configure_global_logger
from project_otto.frames import (
    TurretBaseReferencePointFrame,
    TurretPitchReferencePointFrame,
    TurretYawReferencePointFrame,
    WorldFrame,
)
from project_otto.framesources import (
    RealsenseConfig,
    RealsenseFramesetSource,
    hardware_reset,
    reset_usb_connection,
)
from project_otto.graphics import DebugRenderer
from project_otto.handlers import (
    OdometryMessageHandler,
    RebootMessageHandler,
    RefereeRobotIDMessageHandler,
    SelectNewTargetMessageHandler,
    ShutdownMessageHandler,
)
from project_otto.host_communications import RobotIdentityManager, SelectNewTargetRequestManager
from project_otto.messages import AutoAimTargetUpdateMessage
from project_otto.odometry import OdometryState
from project_otto.robomaster import TeamColor
from project_otto.robot_clustering import RobotClusterer
from project_otto.spatial import (
    LinearUncertainty,
    MeasuredPosition,
    Orientation,
    Position,
    Transform,
    Vector,
)
from project_otto.target_detector import (
    CameraRelativeDetectedTargetSet,
    DetectedTargetPosition,
    LightningTargetDetector,
    WorldDetectedTargetSet,
    prune_invalid_targets,
)
from project_otto.target_selection import (
    IdentityRule,
    TargetSelector,
    TargetSelectorUpdateState,
    TurretDistanceRule,
    TurretRotationDifferenceRule,
    select_target,
)
from project_otto.target_tracker import OpenCVKalmanTrackedTarget, TargetTracker
from project_otto.time import TimestampedHistoryBuffer
from project_otto.timestamps import JetsonTimestamp, OdometryTimestamp
from project_otto.transform_providers import ApplicationTransformProvider
from project_otto.uart import PerseveringReceiver, RxHandler, Serial, Transceiver
from project_otto.update_rate_monitor import UpdateRateMonitor
from project_otto.webserver import StreamingHandler


class CommandlineOptions:
    """
    Commandline options for the main application.
    """

    config_paths: List[str]
    is_silent: bool
    verbosity: int

    def __init__(self, argparse_namespace: argparse.Namespace):
        self.config_paths = argparse_namespace.config_paths
        self.is_silent = argparse_namespace.silent
        self.verbosity = logging.getLevelName(argparse_namespace.verbose)


def _positions_to_robot_targets(
    detection_confidence: float,
    team_color: TeamColor,
    uncertainty: LinearUncertainty[WorldFrame],
    positions: Sequence[Position[WorldFrame]],
) -> Set[DetectedTargetPosition[WorldFrame]]:
    return set(
        DetectedTargetPosition(detection_confidence, team_color, MeasuredPosition(x, uncertainty))
        for x in positions
    )


class MainApplication:
    """
    The top-level Project Otto application.
    """

    def __init__(self, config: ApplicationConfiguration, cli_config: CommandlineOptions):
        self._config = config
        self._cli_config = cli_config
        # TODO: add to config file once defaults are supported
        # https://gitlab.com/aruw/vision/project-otto/-/issues/162
        self._realsense_config = RealsenseConfig()

        self._target_selection_request_manager = SelectNewTargetRequestManager()
        self._robot_identity_manager = RobotIdentityManager()
        self._selected_target: Optional[OpenCVKalmanTrackedTarget] = None

        self._update_rate_monitor = UpdateRateMonitor()
        self._is_initialized = False

    def initialize(self):
        """
        Performs one-time initialization of the system.

        This includes preparing all internal state and opening connections to remote devices like
        the RealSense or serial port. Starts background threads as needed.
        """
        if self._is_initialized:
            raise RuntimeError("Application already initialized but initialize() called again")

        log_selector = LogDirectorySelector(self._config.logging)
        log_selector.create_root_save_dir()

        # Give the logger a temporary configuration which logs to a shared file. The "real" config
        # will give it a proper per-session target file. However, we want _something_ in case it
        # errors.
        fallback_txt_log_path = os.path.join(self._config.logging.root_dir, "early_load_log.txt")
        configure_global_logger(
            fallback_txt_log_path,
            JetsonTimestamp.get_current_time,
            self._cli_config.is_silent,
            self._cli_config.verbosity,
        )

        logging.info("Beginning pre-initialization for new session ====================")

        self._log_dir = log_selector.create_log_dir()

        if self._log_dir is not None:
            txt_log_path = os.path.join(self._log_dir, "log.txt")
            logging.info(f"Transitioning to new log file {txt_log_path}")
            configure_global_logger(
                txt_log_path,
                JetsonTimestamp.get_current_time,
                self._cli_config.is_silent,
                self._cli_config.verbosity,
            )
        else:
            logging.error("Failed to initialize log directory, continuing with shared log file...")

        start_time = perf_counter()
        logging.info("Beginning initialization")

        _ = torch.set_grad_enabled(False)

        self._odom_buffer = TimestampedHistoryBuffer[JetsonTimestamp, OdometryState].from_config(
            self._config.odometry_buffer
        )

        if self._log_dir:
            self._video_dumper = DiskVideoDumper(self._log_dir, self._config.video_dumper)
        else:
            logging.error("Failed to create logging dir, video dumper will not be enabled")
            self._video_dumper = None

        logging.info("Initializing RealSense...")
        if self._config.realsense_reset.reset_usb:
            reset_usb_connection(
                self._config.realsense_reset.vendor_id, self._config.realsense_reset.product_id
            )
        if self._config.realsense_reset.reset_hardware:
            hardware_reset()
        self._frameset_source = RealsenseFramesetSource(self._realsense_config)

        logging.info("Opening MCB UART port...")
        self._mcb_comms_serial = Serial.from_config(self._config.mcb_comms)
        self._mcb_comms = Transceiver(
            self._config.mcb_comms,
            self._build_message_handlers(),
            self._mcb_comms_serial,
            JetsonTimestamp.get_current_time,
        )
        self.mcb_comms_persevering_receiver = PerseveringReceiver(
            self._mcb_comms, self._config.persevering_receiver.max_num_parse_errors
        )

        logging.info("Starting comms thread...")
        self._uart_thread = Thread(
            name="mcb_uart_thread",
            target=self.mcb_comms_persevering_receiver.process_in,
            daemon=True,
        )
        self._uart_thread.start()

        logging.info("Loading detector model...")
        self._detector = LightningTargetDetector.from_weights_checkpoint(self._config.detector)

        logging.info(f"Starting webserver on localhost:{self._config.server.port}...")
        self._streaming_handler = StreamingHandler(
            self._config.server.stream_fps, self._config.server.jpeg_quality
        )
        self._webserver = http.server.HTTPServer(
            ("0.0.0.0", self._config.server.port),
            self._streaming_handler,  # type: ignore
        )
        self._webserver.timeout = self._config.server.timeout.duration_seconds
        self._webserver_thread = Thread(
            name="webserver_thread", target=self._webserver.serve_forever, daemon=True
        )
        self._webserver_thread.start()

        logging.info("Initializing Trackers...")

        self._plate_tracker = TargetTracker(
            self._config.tracker, self._config.target_estimation, OpenCVKalmanTrackedTarget
        )

        self._robot_clusterer = RobotClusterer[OpenCVKalmanTrackedTarget].from_config(
            self._config.robot_clusterer
        )

        self._robot_tracker = TargetTracker(
            self._config.tracker, self._config.target_estimation, OpenCVKalmanTrackedTarget
        )

        self._target_selector = TargetSelector[OpenCVKalmanTrackedTarget](
            BeybladeIdentifier[OpenCVKalmanTrackedTarget](self._config.beyblade_identifier),
            max_radius=self._config.target_selector.max_radius,
        )

        end_time = time.perf_counter()
        logging.info(f"Initialization complete after {end_time-start_time:.2f}s")

        self._is_initialized = True

    def terminate(self):
        """
        Releases resources that the application is using and prepares for exit.
        """
        self._mcb_comms_serial.close()
        self._webserver.shutdown()
        self._webserver.server_close()

    def __enter__(self):
        """
        Context manager entry. Initializes app if not already initialized.
        """
        if not self._is_initialized:
            self.initialize()
        return self

    def __exit__(
        self,
        exc_type: Optional[Type[BaseException]],
        exc_val: Optional[BaseException],
        exc_tb: Optional[TracebackType],
    ):
        """
        Context manager exit. Terminates application.
        """
        self.terminate()

    def _build_message_handlers(self) -> Sequence[RxHandler[Any, JetsonTimestamp]]:
        return [
            OdometryMessageHandler(self._odom_buffer),
            RebootMessageHandler(),
            ShutdownMessageHandler(),
            SelectNewTargetMessageHandler(self._target_selection_request_manager),
            RefereeRobotIDMessageHandler(self._robot_identity_manager),
        ]

    def _build_robot_selector(
        self,
        transform_provider: ApplicationTransformProvider,
    ) -> Callable[[Sequence[OpenCVKalmanTrackedTarget]], Optional[OpenCVKalmanTrackedTarget]]:

        # TODO: pull rules from config, https://gitlab.com/aruw/vision/project-otto/-/issues/163
        rules = [
            (TurretDistanceRule(10, transform_provider), 0.5),
            (TurretRotationDifferenceRule(transform_provider), 2),
        ]

        return lambda targets: select_target(self._config.target_selector, rules, targets)

    def _build_plate_selector(
        self,
        transform_provider: ApplicationTransformProvider,
    ) -> Callable[[Sequence[OpenCVKalmanTrackedTarget]], Optional[OpenCVKalmanTrackedTarget]]:

        # TODO: pull rules from config, https://gitlab.com/aruw/vision/project-otto/-/issues/163
        rules = [
            (TurretDistanceRule(10, transform_provider), 0.5),
            (IdentityRule(self._target_selector.plate_target), 0.25),
        ]

        return lambda targets: select_target(self._config.target_selector, rules, targets)

    def _build_transform_provider(self, odometry: OdometryState) -> ApplicationTransformProvider:
        turret_to_launcher_transform = self._config.identity.turret_reference_to_launcher_transform
        turret_to_camera_transform = self._config.identity.turret_reference_to_camera_transform

        world_to_turret_base_transform = Transform[WorldFrame, TurretBaseReferencePointFrame](
            odometry.position, Orientation[WorldFrame].of_identity()
        )

        turret_base_to_yaw_transform = Transform[
            TurretBaseReferencePointFrame, TurretYawReferencePointFrame
        ](Position[TurretBaseReferencePointFrame].of_origin(), odometry.yaw)

        yaw_to_pitch_transform = Transform[
            TurretYawReferencePointFrame, TurretPitchReferencePointFrame
        ](
            self._config.identity.yaw_reference_to_pitch_reference_transform,
            odometry.pitch,
        )

        return ApplicationTransformProvider(
            turret_reference_point_frame_to_launcher_frame_transform=turret_to_launcher_transform,
            turret_reference_point_frame_to_color_camera_frame_transform=turret_to_camera_transform,
            world_frame_to_turret_base_frame_transform=world_to_turret_base_transform,
            turret_base_frame_to_yaw_reference_point_frame_transform=turret_base_to_yaw_transform,
            yaw_reference_frame_to_pitch_reference_frame_transform=yaw_to_pitch_transform,
        )

    def _send_auto_aim_update_to_host(self, mcb_timestamp: OdometryTimestamp):
        if self._target_selector.target is None:
            self._mcb_comms.send(AutoAimTargetUpdateMessage.without_target(mcb_timestamp))
        else:
            aim_message = AutoAimTargetUpdateMessage.with_target(
                self._target_selector.target.latest_estimated_position,
                self._target_selector.target.latest_estimated_velocity,
                Vector[WorldFrame](0, 0, 0),
                mcb_timestamp,
            )
            self._mcb_comms.send(aim_message)

    def _update_fps_logging(self):
        time_since_fps_log = self._update_rate_monitor.duration_since_reset
        if time_since_fps_log > self._config.core.fps_log_interval:
            average_update_period = self._update_rate_monitor.average_update_period
            if average_update_period is None:
                average_fps = 0
            else:
                average_fps = average_update_period.frequency_hz
            self._update_rate_monitor.reset()

            logging.info(
                f"Average FPS over last {time_since_fps_log.duration_seconds:.2f} seconds: "
                + f"{average_fps:.2f}"
            )
            if average_fps < self._config.core.fps_log_low_fps_threshold:
                logging.warn(f"Average FPS below {self._config.core.fps_log_low_fps_threshold}")

    def run_forever(self):
        """
        Runs Project Otto forever.
        """
        logging.info("Entering main loop...")

        self._update_rate_monitor.reset()

        while True:
            # Check UART status
            if not self._uart_thread.is_alive():
                logging.critical("UART Thread died, terminating...")
                break

            # Receive frames
            frameset = self._frameset_source.wait_for_frames()

            # Save new frame to recording
            if self._video_dumper:
                self._video_dumper.add_frame(frameset)

            # Detect plates
            (detected_plates,) = self._detector.detect_targets([frameset])

            identity = self._robot_identity_manager.identity
            if identity is None:
                logging.warn("No known robot ID, skipping frame processing")
                continue

            # Remove plates which are too small or wrong color
            filtered_plates = prune_invalid_targets(
                identity.color, detected_plates, self._config.plate_filtering
            )

            # Get corresponding odometry
            odometry = self._odom_buffer.search(frameset.time)
            if odometry is None:
                oldest_in_buffer = self._odom_buffer.oldest_timestamp
                latest_in_buffer = self._odom_buffer.latest_timestamp
                logging.warning(
                    f"Frame timestamped at time {frameset.time} not within odometry buffer range."
                    + f" Buffer range is currently: [{oldest_in_buffer}, {latest_in_buffer}]"
                )
                continue

            # Build transforms for current sensor data
            transform_provider = self._build_transform_provider(odometry)

            # Transform detections into 3D world-relative points
            camera_relative_detected_targets = (
                CameraRelativeDetectedTargetSet.from_detected_rectangles(
                    frameset, filtered_plates, self._config.plate_projection_uncertainty
                )
            )
            world_relative_detected_targets = WorldDetectedTargetSet.from_camera_relative(
                camera_relative_detected_targets,
                transform_provider,
                odometry.timestamp,
            )

            # Correlate and update trackers
            self._plate_tracker.update(world_relative_detected_targets)

            self._robot_clusterer.update(
                targets=self._plate_tracker.all_tracked_targets,
                current_time=camera_relative_detected_targets.timestamp,
            )

            # Robots don't have confidence or color, but we need a WorldDetectedTargetSet.
            # TODO: Fix the data structures so that we don't need to build a dummy target set.
            clustered_detected_target_positions = _positions_to_robot_targets(
                detection_confidence=1.0,
                team_color=TeamColor.BLUE,
                uncertainty=LinearUncertainty[WorldFrame].from_variances(
                    *[self._config.robot_uncertainty.robot_position_variance] * 3
                ),
                positions=self._robot_clusterer.centers,
            )

            self._robot_tracker.update(
                WorldDetectedTargetSet(
                    positions=clustered_detected_target_positions,
                    jetson_timestamp=camera_relative_detected_targets.timestamp,
                    odometry_timestamp=odometry.timestamp,
                )
            )

            # Update selected target
            self._target_selector.update(
                TargetSelectorUpdateState(
                    robot_selector=self._build_robot_selector(transform_provider),
                    plate_selector=self._build_plate_selector(transform_provider),
                    robots=self._robot_tracker.all_tracked_targets,
                    plates=self._plate_tracker.all_tracked_targets,
                )
            )

            # Force a reselection if asked
            target_select_message = self._target_selection_request_manager.consume_queued_request()
            if target_select_message is not None:
                logging.info(
                    f"Received target reselection message {target_select_message.request_id}"
                )

                original_target = self._target_selector.robot_target
                self._target_selector.reselect()
                new_target = self._target_selector.robot_target
                original_id = original_target.instance_id if original_target else None
                new_id = new_target.instance_id if new_target else None

                logging.info(f"Performed target reselection: {original_id} -> {new_id}")

            if self._streaming_handler.has_client:
                graphics = DebugRenderer(
                    frameset, transform_provider.camera_frame_to_world_frame_transform.get_inverse()
                )

                # Plate detections
                graphics.render_detected_plates(filtered_plates.plates)
                graphics.render_rejected_detected_plates(
                    detected_plates.plates.difference(filtered_plates.plates)
                )

                # Robot tracking
                graphics.render_estimated_target_positions(
                    self._robot_tracker.all_tracked_targets, is_robot=True
                )
                graphics.render_identities(
                    self._robot_tracker.all_tracked_targets,
                    selected_instance_id=(
                        self._target_selector.robot_target.instance_id
                        if self._target_selector.robot_target
                        else None
                    ),
                    is_active_aim_target=(
                        self._target_selector.target is self._target_selector.robot_target
                    ),
                    is_robot=True,
                )

                # Plate tracking
                graphics.render_estimated_target_positions(
                    self._plate_tracker.all_tracked_targets, is_robot=False
                )
                graphics.render_estimated_plate_velocities(self._plate_tracker.all_tracked_targets)
                graphics.render_estimate_uncertainties(self._plate_tracker.all_tracked_targets)
                graphics.render_identities(
                    self._plate_tracker.all_tracked_targets,
                    selected_instance_id=(
                        self._target_selector.plate_target.instance_id
                        if self._target_selector.plate_target
                        else None
                    ),
                    is_active_aim_target=(
                        self._target_selector.target is self._target_selector.plate_target
                    ),
                    is_robot=False,
                )

                # TODO: graphics.render_plate_selector_scores()

                self._streaming_handler.on_receive_frame(graphics.debug_frame)

            # Send updated target data to MCB
            self._send_auto_aim_update_to_host(odometry.timestamp)

            # Update FPS counters and logging
            self._update_rate_monitor.register_update_complete()
            self._update_fps_logging()


def _build_argument_parser() -> argparse.ArgumentParser:
    """
    Initialize commandline argument parser.
    """
    parser = argparse.ArgumentParser(description="Project-Otto Main Program.")
    _ = parser.add_argument(
        "config_paths",
        metavar="config_filenames",
        type=str,
        help="configuration filenames",
        nargs="*",
    )
    _ = parser.add_argument(
        "-s",
        "--silent",
        action="store_true",
        default=False,
        help="silent mode, suppress all log on screen",
    )
    _ = parser.add_argument(
        "-v",
        "--verbose",
        nargs="?",
        choices=["FATAL", "ERROR", "WARNING", "INFO", "DEBUG"],
        type=str,
        const="DEBUG",
        default="INFO",
        help="Set Logging verbosity level. Default is WARNING.",
    )
    return parser


def main():
    """
    Application entry point.
    """
    parser = _build_argument_parser()
    cli_config = CommandlineOptions(parser.parse_args())

    config_paths = cli_config.config_paths
    config = load_merged_yaml_from_files(config_paths, ApplicationConfiguration)
    try:
        with MainApplication(config, cli_config) as app:
            app.run_forever()
    except Exception:
        logging.critical("Unhandled exception in main", exc_info=True)


if __name__ == "__main__":
    main()
