"""
Timer which remembers when an "update" was registered and computes the average update frequency.
"""

from time import perf_counter_ns
from typing import Callable, Optional

from project_otto.time import Duration

MICROSECONDS_PER_NANOSECOND = 1000


def _default_perf_counter_micros():
    return perf_counter_ns() // MICROSECONDS_PER_NANOSECOND


class UpdateRateMonitor:
    """
    Timer which remembers when an "update" was registered and computes the average update frequency.

    Args:
        get_perf_counter_us:
            A function which returns the current time as microseconds from a high-precision
            monotonic clock. Default is ``time.perf_counter_ns() * MICROSECONDS_PER_NANOSECOND``
    """

    def __init__(
        self,
        get_perf_counter_us: Callable[[], int] = _default_perf_counter_micros,
    ):
        self._get_perf_counter_us = get_perf_counter_us
        self.reset()

    def reset(self):
        """
        Resets stored state as if no updates have yet been registered.
        """
        self._epoch_start_time = self._get_perf_counter_us()
        self._epoch_end_time = self._epoch_start_time
        self._updates_in_epoch = 0

    def register_update_complete(self):
        """
        Records an update as having occurred at the current time.
        """
        self._updates_in_epoch += 1
        self._epoch_end_time = self._get_perf_counter_us()

    @property
    def updates_since_reset(self) -> int:
        """
        The number of times "register_update_complete" has been called since the last reset.
        """
        return self._updates_in_epoch

    @property
    def duration_since_reset(self) -> Duration:
        """
        The amount of time that has elapsed since last reset.

        Measured relative to the most recent update.
        """
        return Duration(self._epoch_end_time - self._epoch_start_time)

    @property
    def average_update_period(self) -> Optional[Duration]:
        """
        The mean interval between updates since the last reset, or None if no updates have occurred.
        """
        if self._updates_in_epoch == 0:
            return None

        return self.duration_since_reset / self._updates_in_epoch
