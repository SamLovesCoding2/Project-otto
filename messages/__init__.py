"""
Provides message classes to be used with UART.

These message classes serialize data into byte strings to be sent to the MCB.
"""

from ._auto_aim_target_update_message import AutoAimTargetUpdateMessage
from ._odometry_message import OdometryMessage
from ._reboot_message import RebootMessage
from ._referee_competition_result_message import RefereeCompetitionResultMessage
from ._referee_realtime_data_message import RefereeRealtimeDataMessage
from ._referee_robot_id_message import RefereeRobotIDMessage
from ._referee_warning_message import RefereeWarningMessage
from ._select_new_target_message import SelectNewTargetMessage
from ._shutdown_message import ShutdownMessage

__all__ = [
    "AutoAimTargetUpdateMessage",
    "OdometryMessage",
    "RefereeRealtimeDataMessage",
    "RefereeCompetitionResultMessage",
    "RefereeWarningMessage",
    "RefereeRobotIDMessage",
    "SelectNewTargetMessage",
    "RebootMessage",
    "ShutdownMessage",
]
