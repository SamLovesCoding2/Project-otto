import json
from dataclasses import asdict
from sqlite3 import connect
from sqlite3.dbapi2 import Connection
from types import TracebackType
from typing import Any, Optional, Type

from project_otto.time import Timestamp
from project_otto.uart import Message

from .._message_store import MessageStore

MESSAGES_TABLE_NAME = "received_host_message_log"


class PersistentMessageStore(MessageStore):
    """
    A MessageStore object that inserts messages into a persistent SQL file on disk.

    Arg:
        path: A String value that represents the path of the SQL file.
    """

    def __init__(self, path: str):
        self._db_connection: Connection = connect(path)
        _ = self._db_connection.execute(
            f"""CREATE TABLE IF NOT EXISTS {MESSAGES_TABLE_NAME}(
                            id INTEGER PRIMARY KEY AUTOINCREMENT,
                            receipt_timestamp INTEGER,
                            message_type INTEGER,
                            message_data STRING
                            )"""
        )
        self._db_connection.commit()

    def close_connection(self):
        """
        Close the connection to the SQL file.
        """
        self._db_connection.close()

    def store_message(self, message: Message, receipt_time: Timestamp[Any]):
        """
        Store the given Message to the SQL database file.

        Arg:
            message: The Message to be stored.
            receipt_time: the time at which this message was received.
        """
        message_data = json.dumps(asdict(message))
        data = [receipt_time.time_microsecs, message.get_type_id(), message_data]

        sub_sql = f"""INSERT INTO {MESSAGES_TABLE_NAME}(
                            receipt_timestamp,
                            message_type,
                            message_data
                            )
                VALUES(?, ?, ?)"""

        with self._db_connection:
            _ = self._db_connection.execute(sub_sql, data)

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
