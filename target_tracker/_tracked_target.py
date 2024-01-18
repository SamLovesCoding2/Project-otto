import abc
from abc import abstractmethod

from project_otto.frames import WorldFrame
from project_otto.spatial import MeasuredPosition, Position, Vector
from project_otto.timestamps import JetsonTimestamp


class TrackedTarget(abc.ABC):
    """
    Represents the 3D position and velocity of a single target (plate).

    This class has an internal state which estimates its position, velocity, and acceleration the
    last time it was updated. It can extrapolate its position into a future timestamp and updates
    its internal state given new positional measurements.
    """

    def __init__(
        self,
        initial_timestamp: JetsonTimestamp,
        instance_id: int,
    ):
        self._latest_observed_timestamp = initial_timestamp
        self._instance_id = instance_id

    @property
    def latest_estimated_position(self) -> Position[WorldFrame]:
        """
        The position estimated at the time of the most recent update.
        """
        raise NotImplementedError

    @property
    def latest_estimated_velocity(self) -> Vector[WorldFrame]:
        """
        The velocity estimated at the time of the most recent update.
        """
        raise NotImplementedError

    @property
    def latest_update_timestamp(self) -> JetsonTimestamp:
        """
        The time at which this target was most recently updated.
        """
        raise NotImplementedError

    @property
    def latest_observed_timestamp(self) -> JetsonTimestamp:
        """
        The time at which this target was most recently observed directly via input measurements.
        """
        return self._latest_observed_timestamp

    @property
    def latest_observed_position(self) -> Position[WorldFrame]:
        """
        The position recently observed directly via input measurements. Unfiltered and noisy.
        """
        return self._latest_observed_position

    @property
    def instance_id(self) -> int:
        """
        A unique ID identifying this tracked target in the enclosing system.
        """
        return self._instance_id

    @abstractmethod
    def extrapolate_position(self, timestamp: JetsonTimestamp) -> Position[WorldFrame]:
        """
        Extrapolates position at some future time.

        Args:
            timestamp: the time to extrapolate position at.
        Returns:
            The estimated position.
        """
        raise NotImplementedError

    @abstractmethod
    def update_from_new_position_measurement(
        self, measurement: MeasuredPosition[WorldFrame], timestamp: JetsonTimestamp
    ):
        """
        Updates position, velocity, and acceleration using measured position and timestamp.

        Args:
            measurement: the newly measured position.
            timestamp: the time to update to.
        """
        self._latest_observed_timestamp = timestamp
        self._latest_observed_position = measurement.position

    @abstractmethod
    def update_from_extrapolation(self, timestamp: JetsonTimestamp):
        """
        Updates target state using un-filtered extrapolation in absence of a new measurement.

        Args:
            timestamp: the time to update to.
        """
        raise NotImplementedError
