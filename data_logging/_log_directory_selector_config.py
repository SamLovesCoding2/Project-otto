from dataclasses import dataclass


@dataclass
class LogDirectorySelectorConfig:
    """
    Configuration for LogDirectorySelector.

    Args:
        root_dir: Root directory for saving logs
        prefix: Prefix for naming each log session directory.
        minimum_index_digits: Minimum index digits for naming each
            log session directory. For indices with less digits than this
            minimum, pad with 0s.
        symlink_name: Name of symlink to point to most recent log session directory.
    """

    root_dir: str
    prefix: str
    minimum_index_digits: int
    symlink_name: str
