from abc import ABC, abstractmethod


class CounterStatistic(ABC):
    """
    Interface for counter_statistics.

    This ABC is an interface for counter_statistics
    """

    @abstractmethod
    def add(self, num: int) -> None:
        """
        Adds `num` to the current statistic value.

        Args:
            num: Integer value to add to the current statistic value
        """
        pass

    @abstractmethod
    def subtract(self, num: int) -> None:
        """
        Subtracts `num` from the current statistic value.

        Args:
            num: Integer value to subtract from the current statistic value
        """
        pass

    @property
    @abstractmethod
    def name(self) -> str:
        """
        The name of the statistic.
        """
        pass
