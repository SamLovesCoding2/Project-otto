import logging
import platform
import subprocess

from project_otto.messages import RebootMessage, ShutdownMessage
from project_otto.timestamps import JetsonTimestamp
from project_otto.uart import RxHandler


class ShutdownMessageHandler(RxHandler[ShutdownMessage, JetsonTimestamp]):
    """
    Handler for Shutdown Message.

    Shuts down the device if it is a Jetson.
    """

    _msg_cls = ShutdownMessage

    def __init__(self):
        pass

    def handle(self, msg: ShutdownMessage, timestamp: JetsonTimestamp):
        """
        Shutdowns.
        """
        if platform.release()[-5:] == "tegra":
            logging.warn("Shutting down...")
            _ = subprocess.call("sudo shutdown now", shell=True)


class RebootMessageHandler(RxHandler[RebootMessage, JetsonTimestamp]):
    """
    Handler for RebootMessage.

    Reboots the device if it is a Jetson.
    """

    _msg_cls = RebootMessage

    def handle(self, msg: RebootMessage, timestamp: JetsonTimestamp):
        """
        Reboots.
        """
        if platform.release()[-5:] == "tegra":
            logging.warn("Rebooting..")
            _ = subprocess.run("sudo reboot", shell=True)
