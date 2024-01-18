import logging

from project_otto.host_communications import RobotIdentityManager
from project_otto.messages import RefereeRobotIDMessage
from project_otto.robomaster import RobotIdentity, RobotType, TeamColor
from project_otto.timestamps import JetsonTimestamp
from project_otto.uart import RxHandler


class RefereeRobotIDMessageHandler(RxHandler[RefereeRobotIDMessage, JetsonTimestamp]):
    """
    Handler for Referee robot ID message.

    Args:
        identity_manager: a manager reference to use when recording updated identity
    """

    _msg_cls = RefereeRobotIDMessage

    def __init__(self, identity_manager: RobotIdentityManager):
        self._manager = identity_manager

    def handle(self, msg: RefereeRobotIDMessage, timestamp: JetsonTimestamp):
        """
        Handle a RefereeRobotIDMessage.

        Get the color and type of the robot based on the input message, then update the information
        in the manager.

        Args:
            msg: a :class:`RefereeRobotIDMessage`.
            timestamp:
                An :class:`JetsonTimestamp` that represents the time that this message was received.
        """
        if 0 <= msg.robot_id < 100:
            color = TeamColor.RED
        elif 100 <= msg.robot_id < 200:
            color = TeamColor.BLUE
        else:
            logging.error(f"Received robot ID {msg.robot_id} out of valid range")
            return

        type_id = msg.robot_id % 100
        try:
            type = RobotType(type_id)
        except ValueError as e:
            logging.error(f"Received invalid robot type ID {type_id}: {str(e)}")
            return

        self._manager.update_robot_identity(RobotIdentity(color, type))

        logging.info(f"Received new robot identity data. Type: {type}. Color: {color}")
