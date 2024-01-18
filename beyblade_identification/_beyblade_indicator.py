from typing import Any, Generic, TypeVar

from project_otto.filters import LowPassFilter, float_interpolation_function
from project_otto.timestamps import Timestamp

T = TypeVar("T", bound=Timestamp[Any])


class BeybladeIndicator(Generic[T]):
    """
    Represents the beyblade indicator state.

    Beyblade indicators compute a boolean value indicating whether its corresponding robot is deemed
    beyblading at the current time step. Two separate low pass filters are maintained. A robot is
    said to be beyblading iff both of the two low pass filters exceed the provided threshold.
    At each time step, a boolean value is provided expected to correspond to whether the magnitude
    of the velocity of a plate relative to the velocity of the associated robot exceeds some
    external threshold. By way of maintaining both a low pass filter with an appropriate
    comparatively high interpolation coefficient and a low pass filter with a low interpolation
    coefficient, we insure that indicators are hesitant to enter the "indicating beyblading" state
    and eager to exit the "indicating beyblading" state.


    Args:
        threshold: the low pass filter threshold over which the beyblade indicator has value
            true.
        initial_time: timestamp for the initial observation of the robot corresponding to the
            beyblade indicator.
        enter_interpolation_coefficient: the slow interpolation coefficient for the
            beyblade indicator.
        exit_interpolation_coefficient: the fast interpolation coefficient for the
            beyblade indicator.
    """

    _threshold: float
    _enter_filter: LowPassFilter[float, T]
    _exit_filter: LowPassFilter[float, T]

    def __init__(
        self,
        threshold: float,
        initial_time: T,
        enter_interpolation_coefficient: float,
        exit_interpolation_coefficient: float,
    ):
        self._threshold = threshold

        initial_value = 0.0

        self._enter_filter = LowPassFilter(
            initial_value,
            initial_time,
            enter_interpolation_coefficient,
            float_interpolation_function,
        )

        self._exit_filter = LowPassFilter(
            initial_value,
            initial_time,
            exit_interpolation_coefficient,
            float_interpolation_function,
        )

    @property
    def value(self) -> bool:
        """Returns: the value of the beyblade indicator."""
        return (
            self._enter_filter.value >= self._threshold
            and self._exit_filter.value >= self._threshold
        )

    def update(self, value: bool, time_step: T):
        """
        Updates the indicator state based on the new value estimate.

        Args:
            value: the observed boolean value corresponding to the threshold relative velocity for
                 the current time step.
        """
        self._enter_filter.update(float(value), time_step)
        self._exit_filter.update(float(value), time_step)
