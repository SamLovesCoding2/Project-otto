"""
Time Domain definitions specific to Project Otto.
"""
from project_otto.time import TimeDomain


class JetsonTimeDomain(TimeDomain):
    """
    Time domain belonging to the Jetson.
    """

    pass


class OdometryTimeDomain(TimeDomain):
    """
    Time domain belonging to the MCB & odometry messages.
    """

    pass
