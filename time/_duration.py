import math
import re
from dataclasses import dataclass

from project_otto.config_deserialization import PrimitiveConfigType

MICROSECONDS_PER_MICROSECOND = 1
MICROSECONDS_PER_MILLISECOND = 1_000
MICROSECONDS_PER_SECOND = 1_000_000
MICROSECONDS_PER_MINUTE = 60_000_000

SUFFIX_TO_MICROSECOND_SCALE_FACTOR = {
    "us": MICROSECONDS_PER_MICROSECOND,
    "ms": MICROSECONDS_PER_MILLISECOND,
    "s": MICROSECONDS_PER_SECOND,
    "m": MICROSECONDS_PER_MINUTE,
}


@dataclass(frozen=True, eq=True)
class Duration:
    """
    Represents a length of time in microseconds.

    Supports various arithmetic and comparison operations with itself and can be added or
    subtracted with Timestamp to produce new Timestamps.

    Args:
        duration_microsecs: length of duration in microseconds
    """

    duration_microsecs: int

    @property
    def duration_seconds(self) -> float:
        """
        Length of this duration in seconds.
        """
        return self.duration_microsecs / MICROSECONDS_PER_SECOND

    @property
    def frequency_hz(self) -> float:
        """
        Returns the frequency, in Hertz, corresponding to this duration as a period.

        If this duration is zero, returns Infinity.
        """
        if self.duration_microsecs == 0:
            return math.inf

        return MICROSECONDS_PER_SECOND / self.duration_microsecs

    @staticmethod
    def from_microseconds(microseconds: int) -> "Duration":
        """
        Returns a new Duration indicating this many microseconds have elapsed.
        """
        return Duration(microseconds)

    @staticmethod
    def from_seconds(seconds: float) -> "Duration":
        """
        Returns a new Duration indicating this many seconds have elapsed.
        """
        return Duration(int(round(seconds * MICROSECONDS_PER_SECOND)))

    @classmethod
    def parse_from_config_primitive(cls, value: PrimitiveConfigType) -> "Duration":
        """
        Parses a Duration from the given string.

        Durations should be formated as an integer or floating-point number followed by a unit
        suffix. Valid suffixes are "us", "ms", "s", and "m".

        Microsecond values cannot be fractional. Fractional components for all other units are
        rounded down to the next microsecond.
        """
        if not isinstance(value, str):
            raise ValueError(f"Duration requires string time spec with units. Got: {repr(value)}")

        def _malformed():
            return ValueError(
                f'Malformed duration, must be number followed by unit suffix. Got: "{value}"'
            )

        structure_match = re.match(r"^([0-9_\.]*)\s*([a-zA-Z]+)$", value)
        if structure_match is None:
            raise _malformed()

        number_string, suffix = structure_match.groups()

        if suffix not in SUFFIX_TO_MICROSECOND_SCALE_FACTOR:
            all_suffixes = list(SUFFIX_TO_MICROSECOND_SCALE_FACTOR.keys())
            raise ValueError(f'Unknown duration suffix "{suffix}". Valid suffixes: {all_suffixes}')

        suffix_scale_factor = SUFFIX_TO_MICROSECOND_SCALE_FACTOR[suffix]

        try:
            number = int(number_string)
        except ValueError:
            if suffix_scale_factor == MICROSECONDS_PER_MICROSECOND:
                raise ValueError(f'Microsecond time specs must be whole integers. Got: "{value}"')

            try:
                number = float(number_string)
            except ValueError:
                raise _malformed()

        total_microseconds = int(number * suffix_scale_factor)
        return Duration(total_microseconds)

    def __add__(self, other: "Duration") -> "Duration":
        """
        Overloads the '+' operator, allowing Durations to be added.

        Args:
            other: the duration to add
        Returns:
            Return a Duration that's the sum of this Duration and another.
        """
        return Duration(self.duration_microsecs + other.duration_microsecs)

    def __sub__(self, other: "Duration") -> "Duration":
        """
        Overloads the '-' operator, allowing Durations to be subtracted.

        Args:
            other: the duration to subtract
        Returns:
            Return a Duration that's the difference between this Duration and another.
        """
        return Duration(self.duration_microsecs - other.duration_microsecs)

    def __mul__(self, scalar: float) -> "Duration":
        """
        Overloads the '*' operator, allowing a scalar to be multipled.

        Args:
            scalar: the multiplying factor
        Returns:
            Return a Duration that's the length of this Duration multiplied by the scalar factor.
        """
        return Duration(int(self.duration_microsecs * scalar))

    def __rmul__(self, scalar: float) -> "Duration":
        """
        Left side reflection of __mul__, allowing a scalar to be multipled.

        Args:
            scalar: the multiplying factor
        Returns:
            Return a Duration that's the length of this Duration multiplied by the scalar factor.
        """
        return Duration(int(round(self.duration_microsecs * scalar)))

    def __truediv__(self, scalar: float) -> "Duration":
        """
        Overloads the '/' operator, allowing this Duration to be divided by a scalar.

        Args:
            scalar: the dividing factor
        Returns:
            Return a Duration that's the length of this Duration divided by a scalar.
        """
        return Duration(int(round(self.duration_microsecs / scalar)))

    def __le__(self, other: "Duration") -> bool:
        """
        Overloads the '<=' operator to compare with other Durations.

        Args:
            other: the other Duration being compared
        Returns:
            Returns if this Duration is shorter then or equal to another
        """
        return self.duration_microsecs <= other.duration_microsecs

    def __lt__(self, other: "Duration") -> bool:
        """
        Overloads the '<' operator to compare with other Durations.

        Args:
            other: the other Duration being compared
        Returns:
            Returns if this Duration is shorter then another
        """
        return self.duration_microsecs < other.duration_microsecs

    def __eq__(self, other: "Duration") -> bool:
        """
        Overloads the '<' operator to compare with other Durations.

        Args:
            other: the other Duration being compared
        Returns:
            Returns if this Duration is equal to another
        """
        return self.duration_microsecs == other.duration_microsecs

    def __abs__(self) -> "Duration":
        """
        Overloads the 'abs()' operator.

        Returns:
            Returns a Duration with the absolute value of this
        """
        return Duration(abs(self.duration_microsecs))

    def __str__(self) -> str:
        """
        Overloads the 'str' operator.

        Returns:
            Returns a str representation
        """
        return f"{self.duration_microsecs} us"
