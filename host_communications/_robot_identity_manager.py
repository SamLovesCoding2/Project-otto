from threading import Lock
from typing import Optional

from project_otto.robomaster import RobotIdentity


class RobotIdentityManager:
    """
    Manager object which remembers the last robot identity and exposes it to the main loop.
    """

    def __init__(self):
        self._identity: Optional[RobotIdentity] = None
        self._lock = Lock()

    def update_robot_identity(self, identity: RobotIdentity):
        """
        Update the current identity.
        """
        with self._lock:
            self._identity = identity

    @property
    def identity(self) -> Optional[RobotIdentity]:
        """
        The most recent identity, or None if no identity information has been received.
        """
        with self._lock:
            return self._identity
