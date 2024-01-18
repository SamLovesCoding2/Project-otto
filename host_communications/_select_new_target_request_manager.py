from dataclasses import dataclass
from threading import Lock
from typing import Optional

from project_otto.messages import SelectNewTargetMessage


@dataclass(frozen=True)
class SelectNewTargetRequest:
    """
    Represents a request from the host to pick a new target.

    Args:
        request_id: an integer representing this request, unique within any session minus wrapping
    """

    request_id: int


class SelectNewTargetRequestManager:
    """
    A stateful handle via which one can notify a client of an incoming target reselection request.

    Used by a message handler to provide requests to the main application. Entirely thread-safe.
    """

    _latest_queued_request: Optional[SelectNewTargetRequest]
    _lock: Lock = Lock()

    def __init__(self):
        self._latest_queued_request = None

    def peek_queued_request(self) -> Optional[SelectNewTargetRequest]:
        """
        Returns the latest request if not yet consumed. None otherwise.
        """
        with self._lock:
            return self._latest_queued_request

    @property
    def has_queued_request(self) -> bool:
        """
        True iff the most recent request has not already been consumed.
        """
        return self.peek_queued_request() is not None

    def consume_queued_request(self) -> Optional[SelectNewTargetRequest]:
        """
        Returns the most recent request. Marks the request as "consumed".

        Future calls to this method or one of the other getters will return None/false until another
        request is received.
        """
        with self._lock:
            latest_request = self._latest_queued_request
            self._latest_queued_request = None
            return latest_request

    def register_new_selection_message(self, msg: SelectNewTargetMessage):
        """
        Saves the given request message.
        """
        with self._lock:
            self._latest_queued_request = SelectNewTargetRequest(msg.request_id)
