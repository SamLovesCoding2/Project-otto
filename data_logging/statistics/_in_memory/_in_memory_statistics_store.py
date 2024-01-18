from typing import Dict

from .._counter_statistic import CounterStatistic
from .._float_statistic import FloatStatistic
from .._statistics_store import StatisticsStore
from ._in_memory_counter_statistic import InMemoryCounterStatistic
from ._in_memory_float_statistic import InMemoryFloatStatistic


class InMemoryStatisticsStore(StatisticsStore):
    """
    Statistics store located in memory.

    Implements StatisticsStore in memory
    """

    def __init__(self):
        self._counter_statistics: Dict[str, int] = {}
        self._float_statistics: Dict[str, float] = {}

    def register_new_counter_statistic(self, name: str) -> CounterStatistic:
        """
        Registers a new int statistic in the StatisticsStore.

        Args:
            name: Name of new statistic to be registered
            (raises an exception if name already registered)
        Returns:
            Returns a CounterStatstic
        """
        if name in self._counter_statistics:
            raise ValueError(f'Counter statistic with name "{name}" already registered')
        new_statistic: CounterStatistic = InMemoryCounterStatistic(name, self._counter_statistics)
        self._counter_statistics[name] = 0
        return new_statistic

    def register_new_float_statistic(self, name: str) -> FloatStatistic:
        """
        Registers a new float statistic in the StatisticsStore.

        Args:
            name: Name of new statistic to be registered
            (raises an exception if name already registered)
        Returns:
            Returns a FlotStatistic
        """
        if name in self._float_statistics:
            raise ValueError(f'Float statistic with name "{name}" already registered')
        new_statistic: FloatStatistic = InMemoryFloatStatistic(name, self._float_statistics)
        self._float_statistics[name] = 0.0
        return new_statistic

    def get_int(self, name: str) -> int:
        """
        Returns the int value stored in given counter_statistic.

        Args:
            name: Name of counter_statistic whose statistic value to be returned
            (raises an exception if there is no counters_statistic named name)
        Returns:
            Returns the int data stored in given counter_statistic.
        """
        val = self._counter_statistics.get(name)
        if val is None:
            raise ValueError(f'No Counter statistic with name "{name}"')
        return val

    def get_float(self, name: str) -> float:
        """
        Returns the float value stored in given float_statistic.

        Args:
            name: Name of float_statistic whose statistic value to be returned
            (raises an exception if there is no float_statistic named name)
        Returns:
            Returns the float value stored in given float_statistic.
        """
        val = self._float_statistics.get(name)
        if val is None:
            raise ValueError(f'No Float statistic with name "{name}"')
        return val
