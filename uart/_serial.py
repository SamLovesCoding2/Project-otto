from abc import ABC, abstractmethod
from dataclasses import dataclass

import serial  # type: ignore


@dataclass
class SerialConfiguration:
    """Configuration for the uart module."""

    port_name: str
    baud_rate: int


class SerialPortOpenException(RuntimeError):
    """
    Exception thrown when the user opens a serial port which returns an error upon connection.

    Args:
        port_name: the serial port path or identifier
        baud_rate: the baud rate used when opening the port
    """

    def __init__(self, port_name: str, baud_rate: int):
        super(SerialPortOpenException, self).__init__(
            f"Failed to open serial port {port_name} for baud rate {baud_rate}"
        )


class AbstractSerial(ABC):
    """
    Abstract serial class. Used only for unit testing the UART. Refer to the Serial class below.
    """

    @property
    @abstractmethod
    def in_waiting(self) -> int:
        """
        Returns number of bytes in the receiver buffer.
        """
        pass

    @abstractmethod
    def read(self, size: int = 1) -> bytes:
        """
        Returns size bytes from port.
        """
        pass

    @abstractmethod
    def write(self, data: bytes):
        """
        Sends bytes through port.
        """
        pass

    @abstractmethod
    def close(self):
        """
        Closes port.
        """
        pass


class Serial(AbstractSerial):
    """
    Simple type-explicit wrapper for serial.Serial library object.

    Raises:
        SerialPortOpenException: if the port was not opened successfully
    """

    def __init__(self, port_name: str, baud_rate: int):

        try:
            self.port = serial.Serial(
                port_name,
                baudrate=baud_rate,
                parity=serial.PARITY_NONE,
                stopbits=serial.STOPBITS_ONE,
                timeout=None,
            )

            if not self.port.is_open:
                self.port.open()
        except serial.SerialException as e:  # pyright: ignore[reportUnknownVariableType]
            raise SerialPortOpenException(port_name, baud_rate) from e

    @classmethod
    def from_config(cls, config: SerialConfiguration):
        """
        Creates a Serial from the provided config parameters.
        """
        return cls(port_name=config.port_name, baud_rate=config.baud_rate)

    @property
    def in_waiting(self) -> int:
        """
        Returns number of bytes in receiving buffer.
        """
        in_waiting: int = self.port.in_waiting
        return in_waiting

    def read(self, size: int = 1) -> bytes:
        """
        Returns size bytes from buffer.
        """
        data: bytes = self.port.read(size)
        return data

    def write(self, data: bytes):
        """
        Sends bytes through port.
        """
        _: int = self.port.write(data)

    def close(self):
        """
        Closes port.
        """
        self.port.close()
