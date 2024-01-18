from abc import ABC, abstractmethod


class FloatStatistic(ABC):
    """
    Interface for float_statistics.

    This ABC is an interface for float_statistics
    """

    @abstractmethod
    def add(self, num: float) -> None:
        """
        Adds `num` to the current statistic value.

        Args:
            num: Float value to add to the current statistic value
        """
        pass

    @abstractmethod
    def subtract(self, num: float) -> None:
        """
        Subtracts `num` from the current statistic value.

        Args:
            num : Float value to subtract from the current statistic value
        """
        pass

    @property
    @abstractmethod
    def name(self) -> str:
        """
        The name of the statistic.
        """
        pass
