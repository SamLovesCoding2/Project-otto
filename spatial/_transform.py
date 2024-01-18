from typing import Any, Generic, TypeVar

import transforms3d  # type: ignore
from numpy.typing import NDArray

from ._frame import Frame
from ._linear_uncertainty import LinearUncertainty
from ._measured_position import MeasuredPosition
from ._orientation import Orientation
from ._position import Position
from ._vector import Vector

# Ideally, we'd more strongly type NumPy arrays. However, there isn't a clear way to do this
# "correctly" while taking np arrays as inputs which might have arbitrary type.
NpArray = NDArray[Any]

SourceFrame = TypeVar("SourceFrame", bound="Frame")
TargetFrame = TypeVar("TargetFrame", bound="Frame")
NewTargetFrame = TypeVar("NewTargetFrame", bound="Frame")


def _rotate_vector(vector: Vector[Any], rotation: Orientation[Any]) -> Vector[Any]:
    rotated_coords: NpArray = transforms3d.quaternions.rotate_vector(
        vector.as_tuple(), rotation.as_tuple()
    )
    return Vector.from_values(rotated_coords)


def _rotate_orientation(
    initial_orientation: Orientation[Any], rotation: Orientation[Any]
) -> Orientation[Any]:
    rotated_coords: NpArray = transforms3d.quaternions.qmult(
        initial_orientation.as_tuple(), rotation.as_tuple()
    )
    return Orientation.from_values(rotated_coords)


class Transform(Generic[SourceFrame, TargetFrame]):
    """
    Represents a transformation from one coordinate frame to another.

    A Transform from frame A to frame B defines a relationship between the two frames, such that a
    spatial measurement in frame A can be represented equivalently in frame B by applying a
    translational and rotational offset. This process is known as *applying* a transform.

    Transforms are specified as a translation and rotation of some "target" frame relative to some
    "source" frame. The "translation" is the target frame's origin in source frame, and the
    "rotation" is the target frame's orientation relative to the source frame's orientation.

    Conceptually, translations are applied "before" rotations: a rotation does not affect the origin
    point of the target frame, only rotates the axes of that frame.

    Although the information in a Transform is sufficient to define the inverse (target-to-source)
    transform, this capability is not provided by default. If this is required, an
    equivalent-but-inverse transform should be constructed in addition to the "forward" version.

    Args:
        translation: the position of the child (target) frame's origin in the source frame
        rotation: the orientation of the child (target) frame relative to the source frame
    """

    _translation: Position[SourceFrame]
    _rotation: Orientation[SourceFrame]

    def __init__(
        self,
        translation: Position[SourceFrame],
        rotation: Orientation[SourceFrame],
    ):
        self._translation = translation
        self._rotation = rotation

    @property
    def translation(self) -> Position[SourceFrame]:
        """This Transform's translational component, as an origin position in the source frame."""
        return self._translation

    @property
    def rotation(self) -> Orientation[SourceFrame]:
        """This Transform's rotational component, as an orientation of the target frame."""
        return self._rotation

    def apply_to_vector(self, vector: Vector[SourceFrame]) -> "Vector[TargetFrame]":
        """
        Transforms the given vector into an equivalent one in the target frame.

        Unlike transforming a Position, this operation *does not* alter the magnitude of the
        components. Vectors' quantities are assumed to be independent of the frame they are in.
        Thus, this function only rotates the provided vector.

        Args:
            vector: a vector to transform

        Returns: a vector equivalent to the original, but in the new frame
        """
        reverse_rotation: Orientation[TargetFrame] = self.rotation.conjugate()

        return _rotate_vector(vector, reverse_rotation)

    def apply_to_position(self, position: Position[SourceFrame]) -> "Position[TargetFrame]":
        """
        Transforms the given position into an equivalent one in the target frame.

        The position will be translated and rotated such that the returned position represents the
        same point as the original, but as if perceived in the target frame.

        Args:
            position: a position to transform

        Returns: a position equivalent to the original, but in the new frame
        """
        un_rotated: Vector[SourceFrame] = Vector(
            position.x - self.translation.x,
            position.y - self.translation.y,
            position.z - self.translation.z,
        )
        rotated = self.apply_to_vector(un_rotated)
        return Position(*rotated.as_tuple())

    def apply_to_linear_uncertainty(
        self, uncertainty: LinearUncertainty[SourceFrame]
    ) -> "LinearUncertainty[TargetFrame]":
        """
        Transforms the given uncertainty into an equivalent one in the target frame.

        Both variance and covariance terms will be modified, so as to preserve the original expected
        distribution along each axis.

        Args:
            uncertainty: a variance matrix to transform

        Returns: an uncertainty equivalent to the original, but in the new frame
        """
        rotation_matrix = self.rotation.as_matrix()
        return LinearUncertainty(rotation_matrix @ uncertainty.covariance @ rotation_matrix.T)

    def apply_to_measured_position(
        self, measurement: MeasuredPosition[SourceFrame]
    ) -> "MeasuredPosition[TargetFrame]":
        """
        Transforms the given measured position into an equivalent one in the target frame.

        Equivalent to individually transforming the position and uncertainty components.

        Args:
            measurement: a measurement to transform

        Returns: a measurement equivalent to the original, but in the new frame
        """
        return MeasuredPosition(
            self.apply_to_position(measurement.position),
            self.apply_to_linear_uncertainty(measurement.uncertainty),
        )

    def get_inverse(self) -> "Transform[TargetFrame, SourceFrame]":
        """
        Returns the inverse of this transform.

        This function should only be used in the transform provider.

        Returns: the inverse of this transform
        """
        pos_x, pos_y, pos_z = self.translation.as_tuple()

        # The inverse of a rotation is its conjugate.
        rot_inverse: Orientation[TargetFrame] = self.rotation.conjugate()

        # The inverse of a translation is the opposite of the original
        # translation with the inverse rotation applied to it.
        pos_negation: Position[TargetFrame] = Position.from_values((-pos_x, -pos_y, -pos_z))
        pos_inverse: Position[TargetFrame] = Position.from_values(
            _rotate_vector(Vector.from_values(pos_negation.as_tuple()), rot_inverse).as_tuple()
        )

        return Transform[TargetFrame, SourceFrame](pos_inverse, rot_inverse)

    def compose(
        self, other: "Transform[TargetFrame, NewTargetFrame]"
    ) -> "Transform[SourceFrame, NewTargetFrame]":
        """
        Computes a new transform equivalent to applying this transform followed by "other".
        """
        # TODO: remove typing ignores
        new_translation = self.get_inverse().apply_to_position(other.translation)
        new_rotation: Orientation[SourceFrame] = _rotate_orientation(
            self.rotation,
            other.rotation,
        )

        return Transform(new_translation, new_rotation)

    @classmethod
    def of_identity(cls) -> "Transform[SourceFrame, TargetFrame]":
        """
        Returns an identity (no-op) transform.
        """
        return Transform[SourceFrame, TargetFrame](
            Position[SourceFrame].of_origin(),
            Orientation[TargetFrame].of_identity(),
        )
