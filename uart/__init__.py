"""
A general purpose UART.

Receives frames as byte strings from a serial interface and sends them to the appropriate message
handlers. Converts messages into byte strings and writes them to the serial interface.
"""

from ._config import PerseveringReceiverConfiguration
from ._crc import compute_table, crc8, crc16
from ._handler import RxHandler
from ._message import Message, ReadableMessage, SerializableMessage
from ._perservering_receiver import PerseveringReceiver
from ._serial import AbstractSerial, Serial, SerialConfiguration
from ._transceiver import MessageParseUnhandledError, Transceiver
from ._transceiver_config import TransceiverConfiguration

__all__ = [
    "Transceiver",
    "Message",
    "SerializableMessage",
    "ReadableMessage",
    "RxHandler",
    "AbstractSerial",
    "Serial",
    "SerialConfiguration",
    "crc8",
    "crc16",
    "compute_table",
    "TransceiverConfiguration",
    "MessageParseUnhandledError",
    "PerseveringReceiver",
    "PerseveringReceiverConfiguration",
]
