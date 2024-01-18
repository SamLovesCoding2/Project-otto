import http.server
import platform
import time
from threading import Lock
from typing import Tuple

import cv2  # type: ignore
import numpy as np
import numpy.typing as npt

BOUNDARY = "FRAMEBOUNDARY"

PAGE = """
<html>
    <head>
        <title>Project Otto Live Debug Server</title>
    </head>
    <body>
        <h1>Project Otto live debug stream: REPLACE</h1>
        <img src="stream.mjpg">
    </body>
</html>
""".replace(
    "REPLACE", platform.node()
)


class StreamingHandler(http.server.BaseHTTPRequestHandler):
    """
    Callable Handler for an http server.

    From Jakob's answer on https://stackoverflow.com/questions/21631799/
    """

    def __init__(self, stream_fps: int, jpeg_quality: int):
        self._frame: npt.NDArray[np.uint8] = np.array(
            [], dtype=np.uint8
        )  # The most recent frame we've received
        self._sent = True  # Whether the most recent frame was sent in the last response
        self._lock = Lock()

        self._encode_params = [int(cv2.IMWRITE_JPEG_QUALITY), jpeg_quality]

        self._frames_received: int = 0
        self._send_every_k_frames: int = int(60 // stream_fps)  # TODO: use time-elapsed instead
        self._num_connections = 0

    def on_receive_frame(self, new_frame: npt.NDArray[np.uint8]) -> None:
        """
        Updates this handler with a new frame.
        """
        with self._lock:
            self._frames_received += 1
            if self._frames_received % self._send_every_k_frames == 0:
                self._frame = new_frame
                self._sent = False

    @property
    def has_client(self) -> bool:
        """
        True iff there is currently a client streaming video from the server.
        """
        with self._lock:
            return self._num_connections > 0

    def __call__(self, *args, **kwargs):  # type: ignore
        """
        Handle a request.
        """
        super().__init__(*args, **kwargs)

    def do_GET(self):  # suppress "function name 'do_GET' should be lowercase": # noqa: N802
        """
        Our reponse to a GET Request.
        """
        if self.path == "/":
            self.send_response(301)
            self.send_header("Location", "/index.html")
            self.end_headers()
        elif self.path == "/index.html":
            content = PAGE.encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "text/html")
            self.send_header("Content-Length", str(len(content)))
            self.end_headers()
            _ = self.wfile.write(content)
        elif self.path == "/stream.mjpg":
            self.send_response(200)
            self.send_header("Age", "0")
            self.send_header("Cache-Control", "no-cache, private")
            self.send_header("Pragma", "no-cache")
            self.send_header("Content-Type", f"multipart/x-mixed-replace; boundary={BOUNDARY}")
            self.end_headers()
            try:
                with self._lock:
                    self._num_connections += 1

                while True:
                    ready = False
                    _bytes = b""
                    with self._lock:
                        if not self._sent:
                            imencode_result: Tuple[bool, bytes] = cv2.imencode(
                                ".jpg", self._frame, self._encode_params
                            )
                            ready, _bytes = imencode_result
                            self._sent = True
                    if ready:
                        self.send_header("Content-Type", "image/jpeg")
                        self.end_headers()
                        _ = self.wfile.write(_bytes)
                        _ = self.wfile.write(b"--" + str.encode(BOUNDARY))
                        _ = self.wfile.write(b"\r\n")
                        self.wfile.flush()
                    time.sleep(0.01)  # TODO: adjust based on profiling (or remove)
            except Exception as e:
                print(e)  # TODO: Log disconnection
            finally:
                with self._lock:
                    self._num_connections -= 1
        else:
            self.send_error(404)
            self.end_headers()
