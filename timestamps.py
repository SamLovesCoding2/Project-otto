"""
Timestamp definitions specific to Project Otto.

Example::

    class TestTimestamp(Timestamp["TestTimestamp"]):
        pass
"""


import time

from project_otto.time import Timestamp
from project_otto.time_domains import JetsonTimeDomain, OdometryTimeDomain


class JetsonTimestamp(Timestamp[JetsonTimeDomain]):
    """
    A timestamp representing the Jetson's clock.

    Subclass of Timestamp. Time is stored in floating point fractions of a second. See
    ._timestamp.py for documentation of methods.
    """

    @classmethod
    def get_current_time(cls):
        """
        Creates a JetsonTimestamp at the current time.

        `clock_gettime` is only supported on UNIX systems.
        """
        nanoseconds_from_epoch: int = time.clock_gettime_ns(time.CLOCK_REALTIME)  # type: ignore
        microseconds_from_epoch = nanoseconds_from_epoch / 1000
        return cls(int(microseconds_from_epoch))


class OdometryTimestamp(Timestamp[OdometryTimeDomain]):
    """
    A timestamp representing the MCB clock.

    Subclass of Timestamp. Time is stored in floating point fractions of a second. See
    ._timestamp.py for documentation of methods.

    """

    pass
