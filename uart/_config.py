from dataclasses import dataclass


@dataclass
class PerseveringReceiverConfiguration:
    """
    Configuration for the perservering receiver.
    """

    max_num_parse_errors: int
