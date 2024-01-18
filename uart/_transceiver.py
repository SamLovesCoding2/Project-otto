import logging
import struct
import warnings
from enum import Enum
from typing import Any, Callable, Dict, Generic, Optional, Sequence, TypeVar

from project_otto.timestamps import Timestamp

from ._crc import crc8, crc16
from ._handler import RxHandler
from ._message import SerializableMessage
from ._message_receiver import HostMessageReceiver
from ._message_transmitter import HostMessageTransmitter
from ._serial import AbstractSerial
from ._transceiver_config import TransceiverConfiguration

# Consts
HEADER_START = b"\xA5"
HEADER_SIZE = 4
MSG_TYPE_SIZE = 2
FOOTER_SIZE = 2

TimestampType = TypeVar("TimestampType", bound="Timestamp[Any]")


class States(Enum):
    """
    Enum for possible internal states of Transceiver class.
    """

    WAITING_FOR_HEADER = 0
    READING_HEADER = 1
    READING_BODY = 2


class MessageParseUnhandledError(Exception):
    """
    Error raised when uart cannot parse a message from the MCB.
    """

    pass


class Transceiver(Generic[TimestampType], HostMessageReceiver, HostMessageTransmitter):
    """
    General purpose UART.

    Collects, parses, and validates byte string packages according to the DJI message protocol.
    Isolates and passes data to appropriate handler using received message type. Can be unit-tested
    without port: internal buffer can be used to mock-receive data and send method also returns
    the sent data.

    Protocol: https://rm-static.djicdn.com/documents/19806/dadf3c8edffa31557376595027431039.pdf

    Args:
        config: a TransceiverConfig specifying threshold of throwaway bytes
        msg_handlers: List of handler objects that the UART can call using their type attribute.
            Returns error if given list contains handlers which share a message type.
            CAUTION: Pyright type checking is essentially disabled for this parameter. Lists should
            be instances of subclasses of Handler and generics of ReadableMessage subclass objects.
            See tests for a rudimentary example.
        serial: Parameter which defines the serial port to read from/write to. Should always be
            _serial.Serial instance in implementation; _serial.AbstractSerial is for unit-testing.
    """

    _config: TransceiverConfiguration

    last_header_receipt_timestamp: TimestampType
    get_current_time: Callable[[], TimestampType]

    # Counts the number of bytes thrown away before finding next header
    _bytes_thrown_away_since_last_message: int = 0
    _bytes_thrown_away_since_last_log: int = 0

    def __init__(
        self,
        config: TransceiverConfiguration,
        msg_handlers: Sequence[RxHandler[Any, TimestampType]],
        serial: AbstractSerial,
        get_current_time: Callable[[], TimestampType],
    ):

        self._config = config

        # Register handlers into dictionary for easy lookup, make sure they don't collide
        self._handler_dict: Dict[int, RxHandler[Any, TimestampType]] = dict()
        for handler in msg_handlers:
            existing_handler = self._handler_dict.get(handler.type_id)
            if existing_handler is not None:
                raise ValueError(
                    f"Given handlers {type(existing_handler).__name__} "
                    + f"and {type(handler).__name__} share a msg type {handler.type_id}."
                )
            else:
                self._handler_dict[handler.type_id] = handler

        self.serial = serial
        self._get_current_time = get_current_time

        self._state = States.WAITING_FOR_HEADER

        # Memory for receiving
        self._msg_len = 0
        self._msg_running_crc16 = 0

    def send(self, msg: "SerializableMessage", seq_num: int = 0):
        """
        Generates byte string package and returns it. If port was given, transmits the package.

        Args:
            msg: message to encode
            seq_num: package sequence number.
        Returns:
            Byte string based on DJI message protocol.
        """
        data = msg.serialize()

        header = HEADER_START
        header += struct.pack("<HB", len(data), seq_num)
        header += struct.pack("B", crc8(header))

        body = struct.pack("<H", msg.get_type_id()) + data
        body += struct.pack("<H", crc16(header + body))

        package = header + body
        self.serial.write(package)

    def process_in(self, max_packets: Optional[int] = None):
        """
        Main receiver method. Attempts to process up to `max_packets` packets.

        Terminates upon completing processing of `max_packet` packets,
        or when no data remains in the serial buffer

        Args:
            max_packets: max number of packets to process
        """
        num_processed_packets: int = 0

        # If blocking, loop forever; else loop until reach max_packets
        while max_packets is None or (
            self.serial.in_waiting != 0 and num_processed_packets < max_packets
        ):

            # Reached max iterations?
            if max_packets is not None:
                if num_processed_packets > max_packets:
                    break

            # Waiting for start of frame
            if self._state == States.WAITING_FOR_HEADER:
                if max_packets is not None and self.serial.in_waiting < 1:
                    break

                if self.serial.read() == HEADER_START:
                    self._state = States.READING_HEADER
                    self.last_header_receipt_timestamp = self._get_current_time()

                    # Print out warning if bytes have been thrown away
                    # when header is found
                    if self._bytes_thrown_away_since_last_message > 0:
                        discarded_bytes = self._bytes_thrown_away_since_last_message
                        logging.warning(
                            f"Incoming UART header found after scanning {discarded_bytes} bytes."
                        )
                        self._bytes_thrown_away_since_last_message = 0
                else:
                    self._bytes_thrown_away_since_last_message += 1
                    self._bytes_thrown_away_since_last_log += 1

                # Over some threshold of bytes have been thrown out
                if (
                    self._bytes_thrown_away_since_last_log
                    > self._config.discarded_bytes_warning_threshold
                ):
                    discarded_bytes = self._bytes_thrown_away_since_last_log
                    logging.warning(
                        f"Threw out {discarded_bytes} bytes waiting for next UART header"
                    )

                    self._bytes_thrown_away_since_last_log = 0

            # Block-process frame header
            if self._state == States.READING_HEADER:

                # Eagerly return if we don't yet have sufficient data queued
                if max_packets is not None and self.serial.in_waiting < HEADER_SIZE:
                    break

                # Read header (blocking if necessary)
                header_bytes = self.serial.read(HEADER_SIZE)
                header = struct.unpack("<HBB", header_bytes)

                self._msg_len = header[0]
                received_crc8 = header[2]

                # Validate header checksum; if fail, reject and drop frame
                calculated_crc8 = crc8(HEADER_START + header_bytes[:3])
                if calculated_crc8 != received_crc8:
                    logging.warning(
                        "Incoming UART header failed CRC check!"
                        + f" Computed {calculated_crc8}, was sent {received_crc8}."
                        + f" Header data: {repr(list(map(hex, header_bytes)))}"
                    )
                    self._state = States.WAITING_FOR_HEADER
                    num_processed_packets += 1
                    continue

                # For memory convenience
                self._msg_running_crc16 = crc16(HEADER_START + header_bytes)

                self._state = States.READING_BODY

            # Block-process message type, message data, and footer
            if self._state == States.READING_BODY:

                # Read message type, data, and footer (blocking if necessary)

                body_size = MSG_TYPE_SIZE + self._msg_len + FOOTER_SIZE
                if max_packets is not None and self.serial.in_waiting < body_size:
                    break

                msg_type_raw = self.serial.read(MSG_TYPE_SIZE)
                msg_data = self.serial.read(self._msg_len)
                received_crc16_raw = self.serial.read(FOOTER_SIZE)

                msg_type = struct.unpack("<H", msg_type_raw)[0]
                received_crc16 = struct.unpack("<H", received_crc16_raw)[0]

                # Validate footer checksum; if fail, reject and drop frame
                self._msg_running_crc16 = crc16(msg_type_raw + msg_data, self._msg_running_crc16)
                if self._msg_running_crc16 != received_crc16:
                    logging.warning(
                        "Incoming UART body failed CRC check!"
                        + f" Computed {self._msg_running_crc16}, was sent {received_crc16}."
                        + f" Dropping {self._msg_len} body bytes."
                    )
                    self._state = States.WAITING_FOR_HEADER
                    num_processed_packets += 1
                    continue

                # Execute appropriate handler
                handler = self._handler_dict.get(msg_type)
                if handler is None:
                    warnings.warn(
                        f"No handler for message of type {msg_type}, data {msg_data}.",
                        RuntimeWarning,
                    )
                else:
                    # Attempt to parse the message
                    try:
                        handler.msg_class.parse(msg_data)
                    # If failed, reset the state of the parser and raise a message parse error
                    # exception
                    except Exception as e:
                        self.reset_states()
                        num_processed_packets += 1
                        raise MessageParseUnhandledError("Unable to parse message.") from e

                    handler.handle(
                        handler.msg_class.parse(msg_data), self.last_header_receipt_timestamp
                    )

                self.reset_states()
                num_processed_packets += 1

    def reset_states(self):
        """
        Clears states in anticipation of receiving further messages.
        """
        self._state = States.WAITING_FOR_HEADER
        self._msg_len = 0
        self._msg_running_crc16 = 0

    @property
    def handler_dict(self):
        """
        Returns dictionary of handlers and msg types.
        """
        return self._handler_dict
