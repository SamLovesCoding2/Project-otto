import warnings
from dataclasses import dataclass
from typing import Any, Collection, Generic, Tuple, Type, TypeVar

import numpy as np
import numpy.typing as npt
import transforms3d  # type: ignore

from project_otto.config_deserialization import PrimitiveConfigType
from project_otto.config_deserialization.utilities import assert_is_list

from ._frame import Frame

# Ideally, we'd more strongly type NumPy arrays. However, there isn't a clear way to do this
# "correctly" while taking np arrays as inputs which might have arbitrary type.
NpArray = npt.NDArray[Any]


InFrame = TypeVar("InFrame", bound="Frame")
NewInFrame = TypeVar("NewInFrame", bound="Frame")


@dataclass
class Orientation(Generic[InFrame]):
    """
    Represents an orientation as a unit quaternion.

    Equivalently, represents a rotation relative to the parent frame.

    Quaternions are defined as a ``(w, x, y, z)`` tuple. The internal representation is always kept
    in normalized form, and thus constructing an Orientation object may alter the component values
    in order to ensure the result is a unit quaternion.

    Args:
        w: *w* component of the quaternion representation of this Orientation.
        x: *x* component of the quaternion representation of this Orientation.
        y: *y* component of the quaternion representation of this Orientation.
        z: *z* component of the quaternion representation of this Orientation.
    """

    w: float
    x: float
    y: float
    z: float

    def __post_init__(self):
        """post-init hook for the @dataclass's generated __init__ function."""
        self._normalize_in_place()

    @staticmethod
    def from_values(
        values: Collection[float], in_frame: Type[InFrame] = Any
    ) -> "Orientation[InFrame]":
        """
        Construct an Orientation from the passed collection of float "values".

        Args:
            values: a four-element tuple, list, numpy array, or other iterable collection. Provided
                values are assumed describe a quaternion and are interpreted in the order
                ``(w, x, y, z)``.
            in_frame: An optional type hint (class type) to constrain the frame of the returned
                Orientation.
        """
        if len(values) != 4:
            raise ValueError(
                "expected quaternion as a four-tuple (w, x, y, z), "
                + f"got object with length {len(values)}"
            )

        values_tuple = tuple(values)
        return Orientation[InFrame](
            values_tuple[0], values_tuple[1], values_tuple[2], values_tuple[3]
        )

    @staticmethod
    def of_identity() -> "Orientation[InFrame]":
        """
        Returns an Orientation representing a null/identity/unit rotation -- "straight ahead".
        """
        return Orientation[InFrame](1, 0, 0, 0)

    def as_tuple(self) -> Tuple[float, float, float, float]:
        """
        Extract the raw values associated with this Orientation's quaternion representation.

        This function should be avoided when possible, as it loses frame-correctness guarantees. If
        possible, perform operations via a Transform such that they retain the associated reference
        frame of involved values.

        Returns:
            The represented quaternion as a tuple of the form ``(w, x, y, z)``.
        """
        return (
            self.w,
            self.x,
            self.y,
            self.z,
        )

    def as_matrix(self) -> NpArray:
        """
        Returns this Orientation represented as a 3x3 rotation matrix.
        """
        mat: NpArray = transforms3d.quaternions.quat2mat(self.as_tuple())
        return mat

    def _normalize_in_place(self):
        norm: float = transforms3d.quaternions.qnorm(self.as_tuple())

        self.w /= norm
        self.x /= norm
        self.y /= norm
        self.z /= norm

    def conjugate(self, in_frame: Type[NewInFrame] = Any) -> "Orientation[NewInFrame]":
        """
        Compute an Orientation representing the reverse rotation.

        The "reverse" orientation describes the orientation of the original reference frame relative
        to the rotated frame that this orientation would describe. For example, if this Orientation
        represents a rotation of positive 45 degrees along the Y axis, the "inverse" would represent
        a rotation of *negative* 45 degrees along the Y axis.

        Applying a rotation and then its reverse is, by design, intended to produce a value
        equivalent to the original.

        Computing the Orientation "reverse" is the quaternion *conjugate*, not the inverse.

        This function is weakly typed with regard to coordinate frames. In theory, the resultant
        value should be interpreted as being in a frame described by the original Orientation's
        rotational transform in its own parent frame. If the original Orientation is the rotational
        component of a rotation-only transform, then the resultant orientation is in the target
        frame of that transform.

        Args:
            in_frame: An optional type hint (class type) to constrain the frame of the returned
                Orientation.

        Returns:
            An Orientation representing the opposite transform of "self".
        """
        arr: NpArray = transforms3d.quaternions.qconjugate(self.as_tuple())
        return Orientation.from_values(arr)

    @staticmethod
    def from_euler_angles(
        roll: float, pitch: float, yaw: float, in_frame: Type[InFrame] = Any
    ) -> "Orientation[InFrame]":
        """
        Converts an euler-angle orientation (in radians) to the equivalent Orientation.

        Rotations are applied in "rotating" frame in the order yaw, pitch, roll. This means that we
        first yaw, then pitch, then roll. The rotations are applied relative to the rotated frame
        at each step.

        Assumes a right-handed coordinate system.

        Args:
            roll: the rotation about the X axis, in radians
            pitch: the rotation about the Y axis, in radians
            yaw: the rotation about the Z axis, in radians

        Returns: An Orientation representing the requested rotation
        """
        quat: NpArray = transforms3d.euler.euler2quat(yaw, pitch, roll, axes="rzyx")
        return Orientation[InFrame](quat[0], quat[1], quat[2], quat[3])

    @staticmethod
    def from_axis_and_angle(
        theta_angle: float, vector: Tuple[float, float, float], in_frame: Type[InFrame] = Any
    ) -> "Orientation[InFrame]":
        """
        Converts an axis-angle orientation (in radians) to the equivalent quaternion.

        Computes an Orientation in the form of Quaternions by converting Axis angle and vector
        in the form of (angle, vector[3,]) into Quaternions that can then be processed to calculate
        Orientation.

        Makes use of an imported library called transforms3d.

        Args:
            theta_angle: angle of rotation around vector. In Radians.
            vector: Vector coordinates associated with the axis angles.
                    MUST be a Tuple of type float.

        Returns:
            An Orientation representing the Quarternion coordinates attained by converting
            angle of rotation around vector to Quaternions. Return Tuple is of size 4 in the
            (w, x, y, z) format.
        """
        # Divide-by-zero is manually caught and triggers a ValueError below.
        # Suppressing the warning for clarity.
        # https://docs.python.org/3/library/warnings.html#temporarily-suppressing-warnings
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            quat_array: NpArray = transforms3d.quaternions.axangle2quat(vector, theta_angle)
        if not np.all(np.isfinite(quat_array)):
            raise ValueError(
                f"Axis-angle form with axis vector {vector} and angle {theta_angle} describes "
                + "undefined orientation"
            )
        return Orientation(quat_array[0], quat_array[1], quat_array[2], quat_array[3])

    @classmethod
    def parse_from_config_primitive(cls, value: PrimitiveConfigType) -> "Orientation[InFrame]":
        """
        Returns an Orientation interpretation of the given human-readable value.

        Expects a three-length list of euler angles, in radians.

        Raises:
            ValueError: if the value is illegal
        """
        values_list = assert_is_list(value, float)

        if len(values_list) != 3:
            raise ValueError(f"Orientation must be a three-element list, got {values_list}")

        roll, pitch, yaw = values_list
        return Orientation.from_euler_angles(roll, pitch, yaw)

    def as_euler_angles(self) -> "EulerOrientation[InFrame]":
        """
        Converts this Orientation into an equivalent EulerOrientation.

        Returns:
            An EulerOrientation representing the euler orientation equivalent of this
            Orientation.
        """
        return EulerOrientation.from_orientation(self)


@dataclass
class EulerOrientation(Generic[InFrame]):
    """
    Represents an orientation as an euler angle with roll, pitch, yaw angle components.

    Equivalently, represents a rotation relative to the parent frame.

    Euler angles  are defined as a ``(roll, pitch, yaw)`` tuple.

    Args:
        roll: roll component of the EulerOrientation.
        pitch: pitch component of the EulerOrientation.
        yaw: yaw component of the EulerOrientation.
    """

    roll: float
    pitch: float
    yaw: float

    def __repr__(self):
        """
        Returns an "instantiation" of the EulerOrientation object in question.
        """
        return f"""EulerOrientation({self.roll}, {self.pitch}, {self.yaw})"""

    def __str__(self):
        """
        Returns roll, pitch, and yaw values rounded to the second decimal in a readable format.
        """
        return f"""roll = {self.roll:.2f}; pitch = {self.pitch:.2f}; yaw = {self.yaw:.2f}"""

    def as_tuple(self) -> Tuple[float, float, float]:
        """
        Extract the raw values associated with the EulerOrientation.

        This function should be avoided when possible, as it loses frame-correctness guarantees. If
        possible, perform operations via a Transform such that they retain the associated reference
        frame of involved values.

        Returns:
            The represented euler angle as a tuple of the form ``(roll, pitch, yaw)``.
        """
        return (self.roll, self.pitch, self.yaw)

    @staticmethod
    def from_orientation(orientation: Orientation[InFrame]) -> "EulerOrientation[InFrame]":
        """
        Converts an Orientation to an EulerOrientation (in radians).

        Args:
            orientation: The Orientation we want to convert.

        Returns: An EulerOrientation representing the requested rotation.
        """
        orientation_tuple = orientation.as_tuple()

        euler: tuple[float] = transforms3d.euler.quat2euler(orientation_tuple, axes="rzyx")

        return EulerOrientation(euler[2], euler[1], euler[0])
