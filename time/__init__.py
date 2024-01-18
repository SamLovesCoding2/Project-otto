"""
A general-purpose timestamp library.

Provides data types for timestamps, durations, and two known timestamp types.

Timestamps ensure that users do not mix up timestamps from different clocks and support a variety
of arithmetic and comparison operators. They can be analogized to wrapper classes around a float.
Durations are simply representations of an amount of time and can be used to modify timestamps.

Timestamps will only work with other timestamps of the same type. Durations are type-agnostic.

Timestamps specific to Project Otto should *not* be included in this module; see the top-level
"timestamps" module. "time" is designed to be application-agnostic.
"""

from ._duration import Duration
from ._time_domain import TimeDomain
from ._timestamp import Timestamp
from ._timestamped_history_buffer import (
    BufferEntryTooOldError,
    TimestampedHistoryBuffer,
    TimestampedHistoryBufferConfiguration,
)

__all__ = [
    "Duration",
    "Timestamp",
    "TimestampedHistoryBuffer",
    "TimestampedHistoryBufferConfiguration",
    "BufferEntryTooOldError",
    "TimeDomain",
]
