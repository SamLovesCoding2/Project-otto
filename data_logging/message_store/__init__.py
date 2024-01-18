"""This library is used to keep track of various statistics around the progam."""
from ._message_store import MessageStore
from ._persistent._persistent_message_store import PersistentMessageStore

__all__ = [
    "MessageStore",
    "PersistentMessageStore",
]
