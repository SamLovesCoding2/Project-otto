from enum import Enum


class RobotType(Enum):
    """
    The type of robot, including which of the three instances of the Standard we are.
    """

    HERO = 1
    ENGINEER = 2
    STANDARD_3 = 3
    STANDARD_4 = 4
    STANDARD_5 = 5
    AERIAL = 6
    SENTRY = 7
    DART = 8
    RADAR = 9
