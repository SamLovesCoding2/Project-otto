"""
"transform provider" types specific to commonly used transforms in Project Otto.

A "transform provider" describes an interface by which an object can "provide" -- i.e., store and
return -- a Transform object between two well-known frames.

Transform providers should be Python "Protocol" implementations. They should be named according to
the specific transformation (parent -> child relationship) they provide, and have a property named
accordingly.

We will later define a class actually implementing all transform protocols. Tests use their own
classes implementing only the Protocols which are relevant to the test domain, while the real robot
deployment will use a combined provider implementing all needed transforms.

Example::

    from typing import Protocol

    from project_otto.frames import CameraRelative, WorldRelative
    from project_otto.spatial import Transform

    class CameraRelativeToWorldRelativeTransformProvider(Protocol):
        @property
        def camera_relative_to_world_relative_transform(
            self,
        ) -> Transform[CameraRelative, WorldRelative]:
            ...
"""
from dataclasses import dataclass
from typing import Protocol

from project_otto.frames import (
    ColorCameraFrame,
    LauncherFrame,
    TurretBaseReferencePointFrame,
    TurretPitchReferencePointFrame,
    TurretReferencePointFrame,
    TurretYawReferencePointFrame,
    WorldFrame,
)
from project_otto.spatial import Transform


@dataclass
class ApplicationTransformProvider:
    """
    The main transform provider for the application.

    This class has various properties which return the specified transforms.
    """

    def __init__(
        self,
        turret_reference_point_frame_to_launcher_frame_transform: Transform[
            TurretReferencePointFrame, LauncherFrame
        ],
        turret_reference_point_frame_to_color_camera_frame_transform: Transform[
            TurretReferencePointFrame, ColorCameraFrame
        ],
        world_frame_to_turret_base_frame_transform: Transform[
            WorldFrame, TurretBaseReferencePointFrame
        ],
        turret_base_frame_to_yaw_reference_point_frame_transform: Transform[
            TurretBaseReferencePointFrame, TurretYawReferencePointFrame
        ],
        yaw_reference_frame_to_pitch_reference_frame_transform: Transform[
            TurretYawReferencePointFrame, TurretPitchReferencePointFrame
        ],
    ):
        pitch_to_turret_reference_transform = Transform[
            TurretPitchReferencePointFrame, TurretReferencePointFrame
        ].of_identity()

        world_frame_to_turret_frame_transform = (
            world_frame_to_turret_base_frame_transform.compose(
                turret_base_frame_to_yaw_reference_point_frame_transform
            )
            .compose(yaw_reference_frame_to_pitch_reference_frame_transform)
            .compose(pitch_to_turret_reference_transform)
        )

        self.world_frame_to_launcher_frame_transform = (
            world_frame_to_turret_frame_transform.compose(
                turret_reference_point_frame_to_launcher_frame_transform
            )
        )

        self.camera_frame_to_world_frame_transform = world_frame_to_turret_frame_transform.compose(
            turret_reference_point_frame_to_color_camera_frame_transform
        ).get_inverse()


class CameraFrameToWorldFrameTransformProvider(Protocol):
    """Provide a Transform from the camera frame to the world frame."""

    @property
    def camera_frame_to_world_frame_transform(
        self,
    ) -> Transform[ColorCameraFrame, WorldFrame]:
        """
        Returns a camera frame to world frame Transform.
        """
        ...


class WorldFrameToLauncherFrameTransformProvider(Protocol):
    """Provide a Transform from the world frame to the launcher frame."""

    @property
    def world_frame_to_launcher_frame_transform(
        self,
    ) -> Transform[WorldFrame, LauncherFrame]:
        """
        Returns a world frame to launcher frame Transform.
        """
        ...
