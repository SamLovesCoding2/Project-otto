from dataclasses import dataclass

from project_otto.time import Duration


@dataclass
class ServerConfiguration:
    """Configuration for the webserver."""

    port: int
    stream_fps: int
    jpeg_quality: int
    timeout: Duration
