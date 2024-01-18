from typing import Dict

from .._float_statistic import FloatStatistic


class InMemoryFloatStatistic(FloatStatistic):
    """
    In memory implementation of FloatStatistic.

    Keeps track of statistics represented as floats in memory.

    Args:
        name: Name of statistic being measured
        float_statistics: Dictionary with all the float statistics
    """

    def __init__(self, name: str, float_statistics: Dict[str, float]):
        self._name: str = name
        self._float_statistics = float_statistics

    def add(self, num: float) -> None:
        """
        Adds `num` to the current statistic value.

        Args:
            num: Float value to add to the current statistic value
        """
        self._float_statistics[self._name] = self._float_statistics[self._name] + num

    def subtract(self, num: float) -> None:
        """
        Subtracts `num` from the current statistic value.

        Args:
            num : Float value to subtract from the current statistic value
        """
        self._float_statistics[self._name] = self._float_statistics[self._name] - num

    @property
    def name(self) -> str:
        """
        The name of the statistic.
        """
        return self._name
