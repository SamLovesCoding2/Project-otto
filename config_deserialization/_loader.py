from typing import Any, Dict, List, Type, TypeVar, Union
from typing import _GenericAlias as TypingGeneric  # type: ignore
from typing import _SpecialForm as TypingSpecial  # type: ignore
from typing import cast, get_args, get_origin, get_type_hints

import numpy as np
import numpy.typing as npt
import yaml

# See https://github.com/clarketm/mergedeep/issues/2
from mergedeep import Strategy, merge  # type: ignore

from ._custom_parse import CustomParseFromConfigPrimitive
from ._type_categories import is_primitive_type, is_special_type

Construct = TypeVar("Construct")


def array_constructor(loader: yaml.FullLoader, node: yaml.SequenceNode) -> npt.NDArray[np.float64]:
    """YAML Constructor for numpy arrays."""
    ar: npt.NDArray[np.float64] = np.array(loader.construct_sequence(node, deep=True))
    return ar


yaml.FullLoader.add_constructor("!array", array_constructor)


def load_yaml_from_str(yaml_str: str, construct: Type[Construct]) -> Construct:
    """
    Parses and typechecks the given YAML string, building the given Python construct.

    Checks against the type annotations annotations in the given Python class (`construct`).

    See :func:`load_from_config_object` for details on how the contents are parsed and typechecked.

    Args:
        yaml_str: The YAML to parse. Expected to be valid YAML, containing values matching the
                  structure and type of the constructed object.
        construct: Python class to build.

    Returns:
        The constructed Python class (of the type passed in as `construct`)

    Raises:
        TypedYAMLLoadMissingError if a key expected in the config is missing in the file
        TypedYAMLLoadInvalidTypeError if a value in the file does not match the expected type
        TypedYAMLLoadCustomParseFailedError if a custom deserializer fails
        ValueError if the file is not valid YAML
    """
    try:
        yaml_parsed = yaml.full_load(yaml_str)
    except yaml.YAMLError as e:
        raise TypedYAMLLoadSyntaxError() from e
    return load_from_config_object(yaml_parsed, construct)


def load_merged_yaml_from_files(file_paths: List[str], construct: Type[Construct]) -> Construct:
    """
    Loads, parses, and typechecks the given YAML files, building the given Python construct.

    Behaves like `load_yaml_from_file` except multiple config files can be passed in, in descending
    order of precedence. The first config file will override the second, which will override the
    third, etc.
    """
    yamls: List[Any] = []
    for file_path in file_paths:
        with open(file_path, "r") as the_file:
            try:
                yamls.append(yaml.full_load(the_file))
            except yaml.YAMLError as e:
                raise TypedYAMLLoadSyntaxError() from e
    merged_yaml: Any = merge({}, *(yamls[::-1]), strategy=Strategy.REPLACE)
    result = load_from_config_object(merged_yaml, construct)
    return result


def load_yaml_from_file(file_path: str, construct: Type[Construct]) -> Construct:
    """
    Loads, parses and typechecks the given YAML file, building the given Python construct.

    Checks against the type annotations annotations in the given Python class (`construct`).

    See :func:`load_from_config_object` for details on how the contents are parsed and typechecked.

    Args:
        file_path: The path of the YAML file to open. Expected to be valid YAML, containing values
                   matching the structure and type of the constructed object.
        construct: Python class to build.

    Returns:
        The constructed Python class (of the type passed in as `construct`)

    Raises:
        TypedYAMLLoadMissingError if a key expected in the config is missing in the file
        TypedYAMLLoadInvalidTypeError if a value in the file does not match the expected type
        TypedYAMLLoadCustomParseFailedError if a custom deserializer fails
        ValueError if the file is not valid YAML
    """
    with open(file_path, "r") as the_file:
        try:
            the_file = yaml.full_load(the_file)
        except yaml.YAMLError as e:
            raise TypedYAMLLoadSyntaxError() from e
        result = load_from_config_object(the_file, construct)
    return result


def _get_parameters(type: Type[Any]) -> Dict[str, Any]:
    signature = get_type_hints(type.__init__)
    _ = signature.pop("return", None)

    return signature


def _strip_generics(type: Type[Any]) -> Type[Any]:
    if isinstance(type, TypingGeneric):
        return cast(Type[Any], get_origin(type))
    return type


def load_from_config_object(value: Any, construct: Type[Construct]) -> Construct:
    """
    Loads, parses, and typechecks the given dictionary of key-value pairs or primitive type.

    Using these values, builds an instance of the Python class specified as the `construct`.
    Typechecks the values against the type annotations as defined in the `construct` class.

    Types that are supported include:
        - Python classes with type annotations
        - Basic types: int, float, bool, str
        - Numpy arrays (float64 dtype)
        - Lists of the above types

    Args:
        value: A dictionary of keys to values to parse, or a leaf node primitive type
        construct: Python class to build

    Returns:
        The constructed Python class (of the type passed in as `construct`)

    Raises:
        TypedYAMLLoadMissingError if a key expected in the config is missing in the file
        TypedYAMLLoadInvalidTypeError if a value in the file does not match the expected type
        TypedYAMLLoadCustomParseFailedError if a custom deserializer fails
        NotImplementedError if attempts to build a structure that is not supported
    """
    construct_base = _strip_generics(construct)

    if is_primitive_type(construct):
        if isinstance(value, construct):
            return value
        else:
            raise TypedYAMLLoadInvalidTypeError(construct, value)
    elif construct == npt.NDArray[np.float64]:
        if isinstance(value, np.ndarray):
            return cast(construct, value.astype("float64"))
        else:
            raise TypedYAMLLoadInvalidTypeError(construct, value)
    elif construct.__module__ == "typing":
        if isinstance(construct, TypingGeneric):
            return _unpack_generic(construct, value)
        elif isinstance(construct, TypingSpecial):
            if construct is Any:
                return value
        raise NotImplementedError(f"Handling type {construct} is currently undefined")
    elif issubclass(construct_base, CustomParseFromConfigPrimitive):
        try:
            return cast(Construct, construct_base.parse_from_config_primitive(value))
        except Exception as e:
            raise TypedYAMLLoadCustomParseFailedError(construct_base, value) from e
    else:
        result_params: Dict[str, Any] = {}
        types: Dict[str, type] = _get_parameters(construct_base)
        for key, type_val in types.items():
            if value is None or key not in value or value[key] is None:
                is_basic_type = (
                    is_primitive_type(type_val)
                    or is_special_type(type_val)
                    or isinstance(type_val, (TypingGeneric, TypingSpecial))
                )
                is_allowed_to_be_missing = (  # is a Union[T, None] or Optional[T]
                    isinstance(type_val, TypingGeneric)
                    and get_origin(type_val) is Union
                    and type(None) in get_args(type_val)
                )
                if hasattr(construct_base, key):
                    result_params[key] = getattr(construct_base, key)
                elif is_allowed_to_be_missing:
                    result_params[key] = None
                elif is_basic_type:
                    raise TypedYAMLLoadMissingError(key, construct, value)
                else:
                    try:
                        # Optional fields can still be populated, so recurse regardless. Errors will
                        # be raised as needed for missing keys.
                        result_params[key] = load_from_config_object({}, construct=type_val)
                    except Exception as e:
                        raise TypedYAMLLoadDictionaryKeyParseError(key, construct) from e
            else:
                try:
                    result_params[key] = load_from_config_object(value[key], construct=type_val)
                except Exception as e:
                    raise TypedYAMLLoadDictionaryKeyParseError(key, construct) from e

        return construct_base(**result_params)


def _unpack_generic(type_val: TypingGeneric, value: Any) -> Any:
    origin = get_origin(type_val)
    if origin is list:
        if not isinstance(value, List):
            raise TypedYAMLLoadInvalidTypeError(type_val, value)
        (expected_item_type,) = get_args(type_val)

        try:
            return _typecheck_list(value, expected_item_type)
        except Exception as e:
            raise TypedYAMLLoadInvalidTypeError(type_val, value) from e
    elif origin is dict:
        if not isinstance(value, Dict):
            raise TypedYAMLLoadInvalidTypeError(type_val, value)
        expected_key_type, expected_value_type = get_args(type_val)

        try:
            return _typecheck_dict(value, expected_key_type, expected_value_type)
        except Exception as e:
            raise TypedYAMLLoadInvalidTypeError(type_val, value) from e
    elif origin is Union:
        possible_types = get_args(type_val)
        for union_type in possible_types:
            is_typing_type = isinstance(union_type, (TypingGeneric, TypingSpecial))
            if is_typing_type or not isinstance(None, union_type):
                try:
                    return load_from_config_object(value, union_type)
                except (
                    TypedYAMLLoadInvalidTypeError,
                    TypedYAMLLoadMissingError,
                ):
                    continue
        raise TypedYAMLLoadInvalidTypeError(type_val, value)
    else:
        raise NotImplementedError(f"Handling type {type_val} is currently undefined")


def _typecheck_list(the_list: List[Any], expected_type: Type[Construct]) -> List[Construct]:
    checked_list: List[Construct] = []
    for item in the_list:
        item = load_from_config_object(item, construct=expected_type)
        checked_list.append(item)
    return checked_list


TKey = TypeVar("TKey")
TValue = TypeVar("TValue")


def _typecheck_dict(
    the_dict: Dict[Any, Any], expected_key_type: Type[TKey], expected_value_type: Type[TValue]
) -> Dict[TKey, TValue]:
    checked_dict: Dict[TKey, TValue] = {}
    for key, value in the_dict.items():
        loaded_key = load_from_config_object(key, construct=expected_key_type)
        loaded_value = load_from_config_object(value, construct=expected_value_type)
        checked_dict[loaded_key] = loaded_value
    return checked_dict


class TypedYAMLLoadMissingError(Exception):
    """Exception raised when a key expected in the constructed class is missing."""

    def __init__(self, key: str, parent_construct: type, parent_dict: Any):
        super().__init__(
            f"Key '{key}' expected on type {parent_construct} but was missing on {parent_dict}"
        )


class TypedYAMLLoadInvalidTypeError(Exception):
    """Exception raised when a value is not the expected type."""

    def __init__(self, expected_type: type, actual_value: Any):
        super().__init__(
            f"Value was supposed to be a {expected_type}, but instead was {repr(actual_value)}"
            + f" ({type(actual_value)})"
        )


class TypedYAMLLoadDictionaryKeyParseError(Exception):
    """Exception raised when a dictionary key fails to parse."""

    def __init__(self, key: str, parent_construct: type):
        super().__init__(f"Parsing key '{key}' on type {parent_construct} failed")


class TypedYAMLLoadCustomParseFailedError(Exception):
    """Exception raised when a custom parser raises an arbitrary exception."""

    def __init__(self, parser_type: type, value: Any):
        super().__init__(f"Custom parser {parser_type} invoked on value {value} failed")


class TypedYAMLLoadSyntaxError(Exception):
    """Exception raised when a YAML parse fails."""

    def __init__(self):
        super().__init__("Syntax error encountered while parsing YAML")
