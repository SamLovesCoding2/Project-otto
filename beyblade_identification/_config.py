from dataclasses import dataclass


@dataclass
class BeybladeIdentifierConfiguration:
    """
    Represents the beyblade identifier configuration state.

    Args:
        max_radius: the maximum radius between a robot target and a given plate target for which the
            robot target and plate target are associated.
        relative_velocity_magnitude_threshold: the magnitude of the relative velocity between a
            given robot target and plate target over which a robot, plate target pair are deemed
            beyblading instantaneously.
        enter_interpolation_coefficient: the slow updating interpolation coefficient for the
            beyblading indicators.
        exit_interpolation_coefficient: the fast updating interpolation coefficient for the
            beyblading indicators.
        indicator_threshold: the low pass filter threshold over which a beyblade indicator has value
            true.
    """

    max_radius: float
    relative_velocity_magnitude_threshold: float
    enter_interpolation_coefficient: float
    exit_interpolation_coefficient: float
    indicator_threshold: float
