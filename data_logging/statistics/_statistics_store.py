from abc import ABC, abstractmethod

from ._counter_statistic import CounterStatistic
from ._float_statistic import FloatStatistic


class StatisticsStore(ABC):
    """
    Interface for StatisticsStores.

    This ABC is an interface from which all StatisticsStores will implement from.
    """

    @abstractmethod
    def register_new_counter_statistic(self, name: str) -> CounterStatistic:
        """
        Registers a new int statistic in the StatisticsStore.

        Args:
            name: Name of new statistic to be registered
            (raises an exception if name already registered)
        Returns:
            Returns a CounterStatstic
        """
        pass

    @abstractmethod
    def register_new_float_statistic(self, name: str) -> FloatStatistic:
        """
        Registers a new float statistic in the StatisticsStore.

        Args:
            name: Name of new statistic to be registered
            (raises an exception if name already registered)
        Returns:
            Returns a FlotStatistic
        """
        pass
