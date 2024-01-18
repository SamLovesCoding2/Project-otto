from math import sqrt
from typing import Any, List, Optional, Set, Tuple, TypeVar

import numpy as np
import numpy.typing as npt

from project_otto.frames import ColorCameraFrame, WorldFrame
from project_otto.image import Frameset
from project_otto.robomaster import TeamColor
from project_otto.spatial import Transform
from project_otto.target_detector import DetectedTargetRegion
from project_otto.target_tracker import OpenCVKalmanTrackedTarget, TrackedTarget

from ._draw_utils import COLORS, draw_line, draw_point, draw_rectangle, draw_text

AnyTrackedTarget = TypeVar("AnyTrackedTarget", bound="TrackedTarget")


class DebugRenderer:
    """
    A class to draw debug images on a frame.

    Args:
        frame: the frame that this class draws on
        world_to_camera_transform: the transformation used to convert from world frame to camera
        frame for drawing.
    """

    def __init__(
        self,
        frame: Frameset[ColorCameraFrame, Any],
        world_to_camera_transform: Transform[WorldFrame, ColorCameraFrame],
    ):
        self.frame = frame
        self.world_to_camera_transform = world_to_camera_transform
        self._debug_frame = frame.color.copy()

    @property
    def debug_frame(self) -> npt.NDArray[np.uint8]:
        """
        The color image with debug annotations added.
        """
        return self._debug_frame

    def render_detected_plates(self, plates: Set[DetectedTargetRegion]):
        """
        Renders detected rectangles on the frame.

        Args:
            plates: A set of detected rectangles.
        """
        for target in plates:
            if target.color == TeamColor.RED:
                draw_rectangle(self._debug_frame, target.rectangle, COLORS.RED)
            else:
                draw_rectangle(self._debug_frame, target.rectangle, COLORS.BLUE)

    def render_rejected_detected_plates(self, rejected_plates: Set[DetectedTargetRegion]):
        """
        Renders rectangles on the frame, marking them as "bad".

        Args:
            rejected_plates: A set of detected rectangles.
        """
        for target in rejected_plates:
            # TODO: draw colored corner points rather than black rectangles
            draw_rectangle(self._debug_frame, target.rectangle, COLORS.BLACK)

    def render_estimated_target_positions(
        self, estimations: List[AnyTrackedTarget], is_robot: bool
    ):
        """
        Renders our estimates of where plates are on the frame.

        Args:
            estimations: The list of target estimates.
            is_robot: True if rendering robot data, False otherwise
        """
        for estimate in estimations:
            image_point = self.frame.position_to_point(
                self.world_to_camera_transform.apply_to_position(estimate.latest_estimated_position)
            )

            draw_point(
                self._debug_frame,
                image_point,
                20 if is_robot else 15,
                COLORS.MAGENTA if is_robot else COLORS.GREEN,
            )

    def render_identities(
        self,
        estimations: List[AnyTrackedTarget],
        selected_instance_id: Optional[int],
        is_active_aim_target: bool,
        is_robot: bool,
    ):
        """
        Renders instance IDs.

        Args:
            estimations: The list of target estimates.
            selected_instance_id: ID of selected target
            is_active_aim_target: True if this target is being aimed at
            is_robot: True if given targets are robots, False otherwise
        """
        for estimate in estimations:
            if estimate.instance_id == selected_instance_id:
                color = COLORS.ORANGE if is_active_aim_target else COLORS.CYAN
            else:
                color = COLORS.WHITE

            draw_text(
                self._debug_frame,
                str(estimate.instance_id),
                self.frame.position_to_point(
                    self.world_to_camera_transform.apply_to_position(
                        estimate.latest_estimated_position
                    )
                ),
                offset=(-10, -60) if is_robot else (-30, -30),
                font_scale=3 if is_robot else 2,
                color=color,
                outline_color=COLORS.BLACK,
            )

    def render_estimate_uncertainties(self, estimations: List[OpenCVKalmanTrackedTarget]):
        """
        Renders the variances for each estimated target.

        Args:
            estimations: The list of target estimates.
        """
        for estimate in estimations:
            x_var = estimate.latest_uncertainty.x
            y_var = estimate.latest_uncertainty.y
            z_var = estimate.latest_uncertainty.z
            draw_text(
                self._debug_frame,
                f"{x_var:.2f}, {y_var:.2f}, {z_var:.2f}",
                self.frame.position_to_point(
                    self.world_to_camera_transform.apply_to_position(
                        estimate.latest_estimated_position
                    )
                ),
                offset=(10, 10),
                thickness=2,
                color=COLORS.WHITE,
                outline_color=COLORS.BLACK,
            )
            total = sqrt(x_var + y_var + z_var)
            draw_text(
                self._debug_frame,
                f"Err: {total:.2f}",
                self.frame.position_to_point(
                    self.world_to_camera_transform.apply_to_position(
                        estimate.latest_estimated_position
                    )
                ),
                offset=(10, -10),
                color=COLORS.WHITE,
                outline_color=COLORS.BLACK,
                outline_thickness=3,
            )

    def render_estimated_plate_velocities(self, estimations: List[AnyTrackedTarget]):
        """
        Renders our estimates of plate velocities on the frame.

        Renders each velocity as three arrows in three dimensions.

        Args:
            estimations: The list of target estimates.
        """
        for estimate in estimations:
            vector = estimate.latest_estimated_velocity
            new_position = estimate.latest_estimated_position + vector
            draw_line(
                self._debug_frame,
                self.frame.position_to_point(
                    self.world_to_camera_transform.apply_to_position(
                        estimate.latest_estimated_position
                    )
                ),
                self.frame.position_to_point(
                    self.world_to_camera_transform.apply_to_position(new_position)
                ),
                COLORS.GREEN,
                arrowhead=True,
            )

    def render_plate_selector_scores(self, scores: List[Tuple[AnyTrackedTarget, Optional[float]]]):
        """
        Renders numerical target selector scores on a debug image.

        Args:
            scores: A list of tuples of the form (target, score)
        """
        for (target, score) in scores:
            if score is not None:
                draw_text(
                    self._debug_frame,
                    f"{score:.2f}",
                    self.frame.position_to_point(
                        self.world_to_camera_transform.apply_to_position(
                            target.latest_estimated_position
                        )
                    ),
                    offset=(10, 10),
                    color=COLORS.ORANGE,
                )
