import logging
import os
import re
from typing import Optional

from ._log_directory_selector_config import LogDirectorySelectorConfig


class LogDirectorySelector:
    """
    Creates the subdirectory to store this session's log data.

    Args:
        config: Log directory selector configuration.
    """

    _config: LogDirectorySelectorConfig

    def __init__(self, config: LogDirectorySelectorConfig):
        self._config = config

    def create_root_save_dir(self):
        """
        Creates the root directory for storing log data.

        Creates the root directory that session subdirectories will be stored in.
        Ignores if the root directory is already created.
        """
        os.makedirs(self._config.root_dir, exist_ok=True)

    def create_log_dir(self) -> Optional[str]:
        """
        Creates and returns path to the new subdirectory for this session's log data.

        The new subdirectory is created within the provided root directory.
        Names subdirectories by timestamp ie. 2021-11-18_16:39:00
        If a subdirectory of the same name exists, increment an index to it ie.
        2021-11-18_16:39:00_1

        Returns:
            Path to log directory
        """
        self.create_root_save_dir()
        save_path = self.get_save_dir_path()
        try:
            os.makedirs(save_path)
            logging.info(f'New logging directory "{save_path}" created')
        except OSError as e:
            logging.error("Failed to create log save directory", exc_info=e)
            return None

        symlink_path = os.path.join(self._config.root_dir, self._config.symlink_name)
        try:
            os.unlink(symlink_path)
        except FileNotFoundError:
            pass  # first time creating symlink
        try:
            os.symlink(save_path, symlink_path)
        except OSError as e:
            logging.error("Failed to symlink new log save directory", exc_info=e)

        return save_path

    def get_save_dir_path(self) -> str:
        """
        Returns the path for the new subdirectory for this session's log data.

        Returns:
            the full path for the new subdirectory using the given root
            directory and list of existing directories.
        """
        existing_dirs = os.listdir(self._config.root_dir)
        indexes = [re.search(f"{self._config.prefix}_(\\d+)", dir) for dir in existing_dirs]
        indexes = [int(x.group(1)) for x in indexes if x]
        indexes.append(0)
        index = max(indexes) + 1
        save_dir = f"{self._config.prefix}_{index:0{self._config.minimum_index_digits}}"
        return os.path.join(self._config.root_dir, save_dir)
