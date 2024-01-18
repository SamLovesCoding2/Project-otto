"""This library is used to keep track of various statistics around the progam."""
from ._counter_statistic import CounterStatistic
from ._float_statistic import FloatStatistic
from ._in_memory._in_memory_counter_statistic import InMemoryCounterStatistic
from ._in_memory._in_memory_float_statistic import InMemoryFloatStatistic
from ._in_memory._in_memory_statistics_store import InMemoryStatisticsStore
from ._persistent._persistent_counter_statistic import PersistentCounterStatistic
from ._persistent._persistent_float_statistic import PersistentFloatStatistic
from ._persistent._persistent_statistics_store import PersistentStatisticsStore
from ._statistics_store import StatisticsStore

__all__ = [
    "FloatStatistic",
    "InMemoryFloatStatistic",
    "InMemoryCounterStatistic",
    "InMemoryStatisticsStore",
    "CounterStatistic",
    "PersistentCounterStatistic",
    "PersistentFloatStatistic",
    "PersistentStatisticsStore",
    "StatisticsStore",
]
