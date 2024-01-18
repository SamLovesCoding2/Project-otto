"""
Frame definitions specific to Project Otto.

Example::

    class CameraRelative(Frame):
        pass
"""
from project_otto.spatial import Frame


class ColorCameraFrame(Frame):
    """
    Frame of reference: the color camera lens on the Realsense.
    """

    pass


class WorldFrame(Frame):
    """
    Frame of reference: the world/odometry frame used by the MCB.

    Odometry measurements sent to us by the MCB are in this frame, and give us the position of the
    TurretFrame.
    """

    pass


class LauncherFrame(Frame):
    """
    Frame of reference: a frame rooted at and in the direction of the turret's barrel.

    Used for analyzing what the turret is facing.
    """

    pass


class TurretReferencePointFrame(Frame):
    """
    Frame of reference: the turret frame of the robot.

    The "reference" position is arbitrary and where exactly it corresponds to mechanically is not
    specified. It must be on the rigid turret assembly. This position is what the MCB's odometry
    defines as the center of the robot, in world frame.
    """

    pass


class TurretYawReferencePointFrame(Frame):
    """
    Frame of reference: A point fixed somewhere on the yaw axis of the turret.

    The "reference" position is arbitrary and where exactly it corresponds to mechanically is not
    specified. If the yaw and pitch axis of a turret overlap, the position should be the same for
    both. Should be in line with the turret frame.

    """

    pass


class TurretPitchReferencePointFrame(Frame):
    """
    Frame of reference: A point fixed somewhere on the pitch axis of the turret.

    This frame comes _after_ the yaw is applied, so it both pitches and yaws with the turret.

    The "reference" position is arbitrary and where exactly it corresponds to mechanically is not
    specified. If the yaw and pitch axis of a turret overlap, the position should be the same for
    both. Should be in line with the turret frame.
    """

    pass


class TurretBaseReferencePointFrame(Frame):
    """
    Frame of reference: A position fixed at the base of the turret.

    This frame is statically positioned on the chassis of the robot.

    The "reference" position is arbitrary and where exactly it corresponds to mechanically is not
    specified. Should have the same rotation as the chassis.
    """
