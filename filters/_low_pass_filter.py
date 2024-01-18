import math
from typing import Any, Callable, Generic, Tuple, TypeVar

from project_otto.timestamps import Timestamp


def float_interpolation_function(alpha: float, xs: Tuple[float, float]) -> float:
    """
    Linearly interpolates between the first element of xs and the second element of xs.

    alpha: the interpolation coefficient.
    xs: tuple, (x0, x1), of values to interpolate between.

    Returns: (1 - alpha) * x0 + alpha * x_1
    """
    x0, x1 = xs
    return (1.0 - alpha) * x0 + alpha * x1


ValueType = TypeVar("ValueType")
TimestampType = TypeVar("TimestampType", bound=Timestamp[Any])


class LowPassFilter(Generic[ValueType, TimestampType]):
    """
    Represents the low pass filter state.

    Args:
        initial_value: the initial value for the low pass filter.
        initial_time: timestamp for the observation of initial_value.
        interpolation_coefficient: the interpolation coefficient, alpha, to use in the standard low
            pass filter update rule given one second has elapsed between the last observation and
            the current observation.
    """

    _lambda: float
    _value: ValueType
    _latest_update_time_stamp: TimestampType
    _interpolation_function: Callable[[float, Tuple[ValueType, ValueType]], ValueType]

    def __init__(
        self,
        initial_value: ValueType,
        initial_time: TimestampType,
        interpolation_coefficient: float,
        interpolation_function: Callable[[float, Tuple[ValueType, ValueType]], ValueType],
    ):
        if not 0.0 < interpolation_coefficient < 1.0:
            raise ValueError(
                f"Expected 0.0 < interpolation_coefficient < 1.0, got {interpolation_coefficient}"
            )
        self._lambda = -math.log(1.0 - interpolation_coefficient)
        self._value = initial_value
        self._latest_update_time_stamp = initial_time
        self._interpolation_function = interpolation_function

    def update(self, value: ValueType, current_time: TimestampType):
        """
        Updates the low pass filter state based on the new observed value and the current time.

        Args:
            value: the observed value for the provided time_step.
        """
        elapsed = max(0.0, (current_time - self._latest_update_time_stamp).duration_seconds)
        alpha = 1.0 - math.exp(-self._lambda * elapsed)
        self._value = self._interpolation_function(alpha, (self._value, value))
        self._latest_update_time_stamp = current_time

    @property
    def latest_update_timestamp(self) -> TimestampType:
        """
        Returns: the timestamp corresponding to the latest update.
        """
        return self._latest_update_time_stamp

    @property
    def value(self) -> ValueType:
        """
        Returns: the current low pass filter value estimate.
        """
        return self._value
