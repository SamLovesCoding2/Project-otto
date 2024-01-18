from dataclasses import dataclass

from project_otto.time import Duration


@dataclass
class RobotClustererConfiguration:
    """
    Represents the RobotClusterer configuration state.

    Args:
        min_radius: the minimum radius between two plates targets for which the plate targets are
            grouped by the target grouper.
        max_radius: the maximum radius between two plates targets for which the plate targets are
            grouped by the target grouper and the maximum radius for which a grouped target is
            associated with a tracked robot.
        relative_velocity_magnitude_threshold: the magnitude of the relative velocity between a
            given robot target and plate target over which a robot, plate target pair are deemed
            beyblading instantaneously.
        interpolation_coefficient: the interpolation coefficient used in updating the
            clustered robot position low pass filter states.
    """

    min_radius: float
    max_radius: float
    age_limit: Duration
    interpolation_coefficient: float
