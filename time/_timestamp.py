from dataclasses import dataclass
from typing import Any, Generic, TypeVar, Union, overload

from ._duration import Duration
from ._time_domain import TimeDomain

Domain = TypeVar("Domain", bound="TimeDomain", covariant=True)


TSelf = TypeVar("TSelf", bound="Timestamp[TimeDomain]")


@dataclass(frozen=True)
class Timestamp(Generic[Domain]):
    """
    Parameterized parent class representing a time stamp.

    Should never be initialized directly. Premade timestamps can be found in timestamps.py

    Supports various arithmetic and comparison operations with Timestamp's with the same TimeType.
    Adding or subtracting Durations produces a new Timestamp of the same type. TimeType represents
    the particular clock type that produces this time stamp. Timestamp's can only interact with
    each other if they have the same clock type. The concept is analogous to "Frame"s for spatial
    coordinates.

    Args:
        time_microsecs: time in microseconds
    """

    time_microsecs: int

    def __add__(self: TSelf, other: Duration) -> TSelf:
        """
        Overloads the '+' operator, allowing Durations to be added.

        Returns the result of adding a Duration time to this Timestamp.

        Args:
            other: the duration to add to this Timestamp
        Returns:
            Return a Timestamp of the same type
        """
        return self.__class__(self.time_microsecs + other.duration_microsecs)

    def __radd__(self: TSelf, other: Duration) -> TSelf:
        """
        Overloads the '+' operator in the reverse direction, allowing Durations to be added.

        Returns the result of adding a Duration time to this Timestamp.

        Args:
            other: the duration to add to this Timestamp
        Returns:
            Return a Timestamp of the same type
        """
        return self.__class__(self.time_microsecs + other.duration_microsecs)

    @overload
    def __sub__(self: TSelf, other: Duration) -> TSelf:
        """
        Overloaded __sub__ method.
        """
        ...

    @overload
    def __sub__(self: TSelf, other: TSelf) -> Duration:
        """
        Overloaded __sub__ method.
        """
        ...

    def __sub__(self: TSelf, other: Any) -> Union[TSelf, Duration]:
        """
        Overloads the '-' operator, allowing Durations/Timestamps to be subtracted.

        The operation is overloaded for two types, subtracting a Duration and subtracting a
        Timestamp. In the case where a Duration is subtracted, produces a Timestamp that's that
        duration earlier then this one. In the case where a Timestamp is subtracted, produces a
        Duration that's the difference between the two Timestamps. This is a subtraction in the
        order in which the two Timestamps are used.

        Args:
            other: Either the duration to subtract from this Timestamp, or
                          the Timestamp to be subtracted from this Timestamp
        Returns:
            If a Duration is passed in, returns a Timestamp of the same type
            If a Timestamp is passed in, returns a Duration representing the difference
        """
        if isinstance(other, Duration):
            return self.__class__(self.time_microsecs - other.duration_microsecs)
        elif isinstance(other, self.__class__):
            return Duration(self.time_microsecs - other.time_microsecs)
        else:
            return NotImplemented

    def __le__(self: TSelf, other: TSelf) -> bool:
        """
        Overloads the '<=' operator to compare with other Timestamps.

        Equivalent to asking if this Timestamp is "no later than" another.

        Args:
            other: the other Timestamp being compared
        Returns:
            Returns if this Timestamp is no later than another
        """
        return self.time_microsecs <= other.time_microsecs

    def __lt__(self: TSelf, other: TSelf) -> bool:
        """
        Overloads the '<' operator to compare with other Timestamps.

        Equivalent to asking if this Timestamp is "earlier then" another.

        Args:
            other: the other Timestamp being compared
        Returns:
            Returns if this Timestamp is earlier then the other
        """
        return self.time_microsecs < other.time_microsecs

    def __eq__(self: TSelf, other: TSelf) -> bool:
        """
        Overloads the '==' operator to compare with other Timestamps.

        Equivalent to asking if this Timestamp is "at the same time as" another.

        Args:
            other: the other Timestamp being compared
        Returns:
            Returns if this Timestamp is at the same time as another
        """
        return type(self) == type(other) and self.time_microsecs == other.time_microsecs

    def __str__(self) -> str:
        """
        Overloads the 'str' operator.

        Returns:
            Returns a str representation
        """
        return f"{self.time_microsecs} us"
