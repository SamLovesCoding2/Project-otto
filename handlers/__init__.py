"""
Provides message handler classes to be used with UART.

These handler classes accept message classes and processes the data they contain.
"""

from ._odometry_message_handler import OdometryMessageHandler
from ._referee_robot_id_message_handler import RefereeRobotIDMessageHandler
from ._select_new_target_message_handler import SelectNewTargetMessageHandler
from ._shutdown_reboot_message_handlers import RebootMessageHandler, ShutdownMessageHandler

__all__ = [
    "OdometryMessageHandler",
    "SelectNewTargetMessageHandler",
    "RebootMessageHandler",
    "ShutdownMessageHandler",
    "RefereeRobotIDMessageHandler",
]
