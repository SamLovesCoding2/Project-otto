from typing import Any, Dict, Protocol, Sequence, Type, TypeVar, Union, runtime_checkable

from ._type_categories import PrimitiveType

PrimitiveConfigType = Union[
    PrimitiveType, Sequence["PrimitiveConfigType"], Dict[Any, "PrimitiveConfigType"]
]

T = TypeVar("T")


@runtime_checkable
class CustomParseFromConfigPrimitive(Protocol[T]):
    """
    When implemented by a type, defines a custom config deserialization strategy.
    """

    @classmethod
    def parse_from_config_primitive(cls: Type[T], value: PrimitiveConfigType) -> T:
        """
        Construct an instance of this class from the given primitive value.

        Raises an exception if the value is illegal.
        """
        ...
