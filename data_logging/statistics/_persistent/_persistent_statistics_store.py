from sqlite3 import IntegrityError, OperationalError, connect
from types import TracebackType
from typing import Any, Callable, Optional, Type

from project_otto.timestamps import JetsonTimestamp, Timestamp

from .._counter_statistic import CounterStatistic
from .._float_statistic import FloatStatistic
from .._statistics_store import StatisticsStore
from ._persistent_counter_statistic import PersistentCounterStatistic
from ._persistent_float_statistic import PersistentFloatStatistic


class PersistentStatisticsStore(StatisticsStore):
    """
    Statistics store on disk by SQLite.

    Implements StatisticsStore that will be stored on disk by SQLite
    """

    def __init__(
        self,
        database_file_path: str,
        get_current_timestamp: Callable[[], Timestamp[Any]] = JetsonTimestamp.get_current_time,
    ):
        """
        Initializes store with a given root directory path and log prefix.

        Args:
            database_file_path:
                File path at which to create the new database. Appends to an existing database if
                already present.
            get_current_timestamp:
                Function which returns the current time when called. Timestamps will be included in
                the store for each operation.
        """
        self._get_current_timestamp = get_current_timestamp

        try:
            self._db_connection = connect(database_file_path)
        except OperationalError as e:
            raise RuntimeError(
                f"Failed to connect to statistics database file at path {database_file_path}. "
                + "Verify that the directory exists and that any file of the same name is a valid "
                + "statistics store file."
            ) from e
        _ = self._db_connection.execute(
            """CREATE TABLE IF NOT EXISTS counter_statistics(
                            id INTEGER PRIMARY KEY AUTOINCREMENT,
                            property TEXT,
                            value INTEGER,
                            operation TEXT,
                            timestamp INTEGER
                            )"""
        )
        _ = self._db_connection.execute(
            """CREATE TABLE IF NOT EXISTS float_statistics(
                            id INTEGER PRIMARY KEY AUTOINCREMENT,
                            property TEXT,
                            value FLOAT,
                            operation TEXT,
                            timestamp INTEGER
                            )"""
        )
        _ = self._db_connection.execute(
            """CREATE TABLE IF NOT EXISTS statistics_registry(
                            id STRING NOT NULL,
                            type BOOLEAN NOT NULL,
                            PRIMARY KEY(id, type)
                            )"""
        )
        self._db_connection.commit()

    def close_connection(self) -> None:
        """
        Closes connection to database.

        Closes connection to database and should be called at end of task/process.
        """
        self._db_connection.close()

    def register_new_counter_statistic(self, name: str) -> CounterStatistic:
        """
        Registers a new counter statistic in the StatisticsStore.

        Args:
            name: Name of new statistic to be registered.
        Returns:
            Returns a CounterStatistic
        Raises:
            ValueError: if name is already registered as a counter statistic
        """
        try:
            with self._db_connection:
                _ = self._db_connection.execute(
                    """INSERT INTO statistics_registry(id, type) VALUES(?,?)""", (name, "int")
                )
                return PersistentCounterStatistic(
                    name, self._db_connection, self._get_current_timestamp
                )
        except IntegrityError:
            raise ValueError(f'Counter statistic with name "{name}" already registered')

    def register_new_float_statistic(self, name: str) -> FloatStatistic:
        """
        Registers a new float statistic in the StatisticsStore.

        Args:
            name: Name of new statistic to be registered.
        Returns:
            Returns a FloatStatistic
        Raises:
            ValueError: if name is already registered as a float statistic
        """
        try:
            with self._db_connection:
                _ = self._db_connection.execute(
                    """INSERT INTO statistics_registry(id, type) VALUES(?,?)""", (name, "float")
                )
                return PersistentFloatStatistic(
                    name, self._db_connection, self._get_current_timestamp
                )
        except IntegrityError:
            raise ValueError(f'Float statistic with name "{name}" already registered')

    def __enter__(self):
        """
        Context manager entry. Returns self.
        """
        return self

    def __exit__(
        self,
        exc_type: Optional[Type[BaseException]],
        exc_val: Optional[BaseException],
        exc_tb: Optional[TracebackType],
    ):
        """
        Context manager exit. Closes database connection.
        """
        self.close_connection()
