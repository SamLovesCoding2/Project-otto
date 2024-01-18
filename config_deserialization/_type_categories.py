from typing import Any, Union

import numpy as np
import numpy.typing as npt

PRIMITIVE_TYPES = (int, float, bool, str)
PrimitiveType = Union[int, float, bool, str]

SPECIAL_TYPES = (npt.NDArray[np.float64],)


def is_primitive_type(type_class: Any):
    """Returns True iff type_class is a primitive type."""
    return type_class in PRIMITIVE_TYPES


def is_special_type(type_class: Any):
    """Returns True iff type_class is a primitive type."""
    return type_class in SPECIAL_TYPES
