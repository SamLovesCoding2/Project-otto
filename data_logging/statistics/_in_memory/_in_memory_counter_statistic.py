from typing import Dict

from .._counter_statistic import CounterStatistic


class InMemoryCounterStatistic(CounterStatistic):
    """
    In memory implementation of CounterStatistic.

    Implements Counterstatistic in memory

    Args:
        name: Name of statistic being measured
        counter_statistics: Dictionary with all counter statistics
    """

    def __init__(self, name: str, counter_statistics: Dict[str, int]):
        self._name: str = name
        self._counter_statistics = counter_statistics

    def add(self, num: int) -> None:
        """
        Adds `num` to the current statistic value.

        Args:
            num: Integer value to add to the current statistic value
        """
        self._counter_statistics[self._name] = self._counter_statistics[self._name] + num

    def subtract(self, num: int) -> None:
        """
        Subtracts `num` from the current statistic value.

        Args:
            num: Integer value to subtract from the current statistic value
        """
        self._counter_statistics[self._name] = self._counter_statistics[self._name] - num

    @property
    def name(self) -> str:
        """
        The name of the statistic.
        """
        return self._name
