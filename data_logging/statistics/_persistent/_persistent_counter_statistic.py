from sqlite3 import Connection
from typing import Any, Callable

from project_otto.timestamps import Timestamp

from .._counter_statistic import CounterStatistic


class PersistentCounterStatistic(CounterStatistic):
    """
    Persistent implementation of CounterStatistic.

    Implements Counterstatistic by SQLite.

    Args:
        name: Name of statistic being measured
        counter_statistics: Dictionary with all counter statistics
        get_current_timestamp: Thunk which returns the current time to be logged in the database
    """

    def __init__(
        self, name: str, conn: Connection, get_current_timestamp: Callable[[], Timestamp[Any]]
    ):
        self._name: str = name
        self._conn: Connection = conn
        self._get_current_timestamp = get_current_timestamp

    def add(self, num: int) -> None:
        """
        Adds `num` to the current statistic value.

        Args:
            num: Integer value to add to the current statistic value
        """
        self._insert_into_database(num, "ADD")

    def subtract(self, num: int) -> None:
        """
        Subtracts `num` from the current statistic value.

        Args:
            num: Integer value to subtract from the current statistic value
        """
        self._insert_into_database(num, "SUB")

    def _insert_into_database(self, num: int, operation: str) -> None:
        """
        Inserts data into sql database.

        Args:
            num: Integer value to be inserted
            operation: Name of operation to be inserted
        """
        timestamp_microsecs = self._get_current_timestamp().time_microsecs
        data = [self._name, num, operation, timestamp_microsecs]
        sub_sql: str = (
            "INSERT INTO counter_statistics(property,value,operation,timestamp) VALUES(?, ?, ?, ?)"
        )
        with self._conn:
            _ = self._conn.execute(sub_sql, data)

    @property
    def name(self) -> str:
        """
        The name of the statistic.
        """
        return self._name
