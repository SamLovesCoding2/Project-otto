from enum import Enum


class TeamColor(Enum):
    """
    The team color of a given target (plate or robot), i.e. red or blue.
    """

    RED = 0
    BLUE = 1

    def flip(self) -> "TeamColor":
        """
        Returns opposite team color.
        """
        if self == TeamColor.BLUE:
            return TeamColor.RED
        else:
            return TeamColor.BLUE
