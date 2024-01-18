from dataclasses import dataclass

from ._robot_type import RobotType
from ._team_color import TeamColor


@dataclass
class RobotIdentity:
    """
    A robot identity, combining a team color and robot typpe.
    """

    color: TeamColor
    type: RobotType
