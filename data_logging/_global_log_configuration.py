import logging
from typing import Any, Callable

from project_otto.time import Timestamp


def configure_global_logger(
    log_file_path: str,
    get_timestamp: Callable[[], Timestamp[Any]],
    is_silent: bool,
    verbosity_level: int,
):
    """
    Configure "logging" module to log data to stdout and log to a text file.

    Args:
        log_file_path: file path to save logs to
        get_timestamp: a function returning the current local time
        is_silent: if we are running on silent mode without stdout output
        verbosity_level: verbosity level of logs, see definitions in logging module
    """
    log_handlers: list[logging.Handler] = [logging.FileHandler(log_file_path)]
    if not is_silent:
        log_handlers.append(logging.StreamHandler())
    logging.basicConfig(
        level=verbosity_level,
        format=(
            "[%(levelname)s %(threadName)s %(jetson_time)d %(filename)s:%(lineno)d:%(funcName)s]"
            + " %(message)s"
        ),
        force=True,
        handlers=log_handlers,
    )

    # From:
    # https://stackoverflow.com/questions/17558552/how-do-i-add-custom-field-to-python-log-format-string
    old_factory = logging.getLogRecordFactory()

    def record_factory(*args, **kwargs):  # type: ignore
        timestamp = get_timestamp().time_microsecs

        record = old_factory(*args, **kwargs)
        record.jetson_time = timestamp  # type: ignore
        return record

    logging.setLogRecordFactory(record_factory)
