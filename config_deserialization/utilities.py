"""
Config deserialization utilities.
"""

from typing import Any, List, Type, TypeVar

from ._custom_parse import PrimitiveConfigType, PrimitiveType

T = TypeVar("T", bound=PrimitiveType)


def assert_is_list(value: PrimitiveConfigType, element_type: Type[T]) -> List[T]:
    """
    Checks whether the value is a list with all elements of the given type.

    Raises:
        ValueError: if the argument is not a list of the specified type

    Returns: the input list, of appropriate type
    """
    if not isinstance(value, list):
        raise ValueError(f"Expected list, got {value}")

    values_list: List[Any] = value
    any_incorrect_type_entries = any((not isinstance(v, element_type) for v in values_list))
    if any_incorrect_type_entries:
        raise ValueError(f"All list elements must be of type {element_type}, got {value}")

    return values_list
