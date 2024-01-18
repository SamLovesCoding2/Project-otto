"""
A general-purpose spatial data representation and transform library.

Provides data types for positions, vectors, and orientations in 3D space.

The associated transformation library facilitates translation of positions and vectors from one
reference frame to another, using provided measurements (typically sensor data) to define the
relationship between the frames.

Every value is generic over the frame it's represented in. Transforms and other intra-frame
operations enforce correct frames of reference for every value involved.

Frames specific to Project Otto should *not* be included in this module; see the top-level "frames"
and "transform_providers" modules. "spatial" is designed to be application-agnostic.
"""

from ._frame import Frame
from ._linear_uncertainty import LinearUncertainty
from ._measured_position import MeasuredPosition
from ._orientation import EulerOrientation, Orientation
from ._position import Position
from ._transform import Transform
from ._vector import Vector

__all__ = [
    "Transform",
    "Position",
    "Vector",
    "LinearUncertainty",
    "MeasuredPosition",
    "Orientation",
    "EulerOrientation",
    "Frame",
]
