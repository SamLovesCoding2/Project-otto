"""
Convenience classes which allow for easy performance profiling.

Example::

    from project_otto.profiler import CProfiler, LProfiler

    def foo(a):
        return a + 1

    def bar(a):
        return foo(a)

    def main():
        i = 0
        with CProfiler("cprof.txt") as _:
            while i < 100000:
                i = foo(i)

        with LProfiler("lprof.txt", foo, bar) as _:
            while True:
                i = bar(i)
"""

from cProfile import Profile
from pstats import SortKey, Stats
from types import TracebackType
from typing import Any, Callable, Optional, Type

from line_profiler import LineProfiler  # type: ignore


class CProfiler(Profile):
    """
    CProfile context manager which writes results to file.

    Args:
        file_path: The text file to write to.
    """

    def __init__(self, file_path: str):
        super().__init__()
        self.file_path = file_path

    def __exit__(self, *exc_info: Any):
        """
        Context manager exit. Disables profiler and prints results to text file.
        """
        self.disable()
        with open(self.file_path, "w") as f:
            stats = Stats(self, stream=f)
            stats = stats.sort_stats(SortKey.CUMULATIVE)
            _ = stats.print_stats()


class LProfiler(LineProfiler):  # pyright: ignore[reportUntypedBaseClass]
    """
    Line profiler context manager allows line-by-line profiling of registered functions.

    Args:
        file_path: The text file to write to.
        args: Functions to profile.
    """

    def __init__(self, file_path: str, *args: Callable[..., Any]):
        super().__init__(*args)
        self._file_path = file_path

    def __enter__(self):
        """
        Context manager enter. Enables profiler.
        """
        self.enable_by_count()
        return self

    def __exit__(
        self,
        exc_type: Optional[Type[BaseException]],
        exc_val: Optional[BaseException],
        exc_tb: Optional[TracebackType],
    ):
        """
        Context manager exit. Disables profiler and prints results to text file.
        """
        self.disable_by_count()
        with open(self._file_path, "w") as f:
            self.print_stats(stream=f)
