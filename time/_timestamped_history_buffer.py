import bisect
from dataclasses import dataclass
from threading import Lock
from typing import Any, Callable, Collection, Generic, List, Optional, TypeVar

from ._duration import Duration
from ._time_domain import TimeDomain
from ._timestamp import Timestamp

Key = TypeVar("Key", bound="Timestamp[TimeDomain]")
Value = TypeVar("Value")


@dataclass
class TimestampedHistoryBufferConfiguration:
    """
    Configuration for a :class:`TimestampedHistoryBuffer`.
    """

    max_entries: int
    maximum_entry_age: Duration


class BufferEntryTooOldError(Exception, Generic[Key]):
    """
    Exception indicating that the provided new entry is too old.

    Raised when an attempted addition to a TimestampedHistoryBuffer had a timestamp key that is
    earlier than the most recent entry already in the buffer.
    """

    def __init__(self, new_timestamp: Key, existing_latest_timestamp: Key):
        self.new_timestamp = existing_latest_timestamp
        super(BufferEntryTooOldError, self).__init__(
            f"Provided entry with timestamp {new_timestamp} is not newer than existing"
            + f" latest timestamp {existing_latest_timestamp}"
        )


class TimestampedHistoryBuffer(Generic[Key, Value]):
    """
    A map-like buffer that allows users to look up entries via their approximate timestamp.

    Entries can be any data type. Searching in the buffer for a timestamp returns the
    timestamp-entry pair closest to the timestamp. Does not support adding timestamps that are
    older than existing.

    Args:
        max_entries: maximum number of timestamp-entry pairs stored. Must be greater than 0.
        max_entry_age_micros:
            maximum time in microseconds that timestamp-entry pairs are stored. Updated whenever
            new timestamp-entry pair is added. Must be greater than 0.
    """

    def __init__(self, max_entries: int, maximum_entry_age: Duration):
        if max_entries <= 0:
            raise ValueError(f"max_entries must be greater than 0, got {str(max_entries)}")
        if maximum_entry_age.duration_microsecs <= 0:
            raise ValueError(f"maximum_entry_age must be greater than 0, got {maximum_entry_age}")

        self._max_entries = max_entries
        self._maximum_entry_age = maximum_entry_age

        self._keys: List[Key] = []
        self._data: List[Value] = []
        self._lock = Lock()

    @classmethod
    def from_config(cls, config: TimestampedHistoryBufferConfiguration):
        """
        Creates a TimestampedHistoryBuffer from the provided config parameters.
        """
        return cls(max_entries=config.max_entries, maximum_entry_age=config.maximum_entry_age)

    def add(self, timestamp: Key, value: Value):
        """
        Adds the specified entry to the front of the queue.

        If the specified time is earlier than or equal to any existing item in the queue, a
        ValueError is thrown. Removes any entries which are older than the
        maximum allowed age. Removes an entry from the end if there are too many entries in the
        queue.

        Raises:
            BufferEntryTooOldError:
                when the given timestamp is not newer than the oldest existing entry

        Args:
            timestamp: the Timestamp to add as a key
            value: an associated value
        """
        with self._lock:
            latest_timestamp = self.latest_timestamp
            if latest_timestamp is not None and timestamp <= latest_timestamp:
                raise BufferEntryTooOldError(timestamp, latest_timestamp)

            self._keys.append(timestamp)
            self._data.append(value)
            self._remove_expired_items(timestamp)

    def clear(self):
        """
        Clears the data queue.
        """
        with self._lock:
            self._data.clear()

    def search(self, timestamp: Key) -> Optional[Value]:
        """
        Finds the closest existing timestamp in the buffer.

        If the asked for timestamp is older then the oldest stored timestamp or newer then the
        newest, then None is returned. Otherwise it finds the
        closest timestamp-entry pair, which could be earlier or later. If both are equally close,
        it returns the later one.

        Args:
            timestamp: the Timestamp to search for
        Returns:
            An Optional value if it exists and None if the timestamp is too old or in the future
        """
        with self._lock:
            latest_timestamp = self.latest_timestamp
            oldest_timestamp = self.oldest_timestamp

            if len(self._data) == 0:
                return None

            if latest_timestamp is None or oldest_timestamp is None:
                return None

            if timestamp < oldest_timestamp or timestamp > latest_timestamp:
                return None

            pos = bisect.bisect_left(self._keys, timestamp)

            if pos == 0:
                return self._data[pos]
            elif pos == len(self._keys):
                return self._data[-1]
            else:
                earlier_t = self._keys[pos - 1]
                later_t = self._keys[pos]
                closest_pos = (
                    pos - 1 if abs(earlier_t - timestamp) < abs(later_t - timestamp) else pos
                )
                return self._data[closest_pos]

    def apply(self, func: Callable[[Key], Any]) -> Collection[Any]:
        """
        Applies a lambda function operating on timestamps to every element in the buffer.

        Returns: a collection of the result of the lambda function
        """
        with self._lock:
            return_collection = [func(key) for key in self._keys]
            return return_collection

    @property
    def num_entries(self) -> int:
        """
        The number of entries currently in the buffer.
        """
        return len(self._data)

    @property
    def oldest_timestamp(self) -> Optional[Key]:
        """
        Returns: the oldest timestamp, None if there are no timestamps.
        """
        if len(self._data) == 0:
            return None
        return self._keys[0]

    @property
    def latest_timestamp(self) -> Optional[Key]:
        """
        Returns: the latest timestamp, None if there are no timestamps.
        """
        if len(self._data) == 0:
            return None
        return self._keys[-1]

    # Helper method to remove all expired timestamps
    def _remove_expired_items(self, latest_timestamp: Key):
        while len(self._data) > self._max_entries or (
            (oldest_timestamp := self.oldest_timestamp)
            and abs(latest_timestamp - oldest_timestamp) > self._maximum_entry_age
        ):
            _ = self._keys.pop(0)
            _ = self._data.pop(0)

    @property
    def max_entries(self) -> int:
        """
        Maximum number of total entries in the buffer, before elements are dropped.
        """
        return self._max_entries

    @property
    def maximum_entry_age(self) -> Duration:
        """
        Age beyond which elements are dropped.
        """
        return self._maximum_entry_age
