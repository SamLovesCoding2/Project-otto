"""
Infrastructure for communicating with a host coprocessor.

On our robots, this is the "Main Control Board" (MCB).
"""

from ._robot_identity_manager import RobotIdentityManager
from ._select_new_target_request_manager import (
    SelectNewTargetRequest,
    SelectNewTargetRequestManager,
)

__all__ = [
    "SelectNewTargetRequestManager",
    "SelectNewTargetRequest",
    "RobotIdentityManager",
]
