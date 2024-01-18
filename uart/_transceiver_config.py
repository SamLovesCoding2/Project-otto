from dataclasses import dataclass


@dataclass
class TransceiverConfiguration:
    """
    Configuration for Transceiver.

    Args:
        discarded_bytes_warning_threshold:
            Number of bytes thrown away before a warning is logged.
    """

    discarded_bytes_warning_threshold: int = 20
