"""Odometry Message."""
import struct
from dataclasses import dataclass
from typing import Iterator, List, Tuple

from project_otto.uart import ReadableMessage


@dataclass
class OdometryMessage(ReadableMessage):
    """
    Message that contains odometry data.

    Args:
        time: a int representing the odometry timestamp of this message
        x_pos: a float that represents the chassis x position
        y_pos: a float that represents the chassis y position
        z_pos: a float that represents the chassis z position
        pitch: a float that represents the chassis pitch
        yaw: a float that represents the chassis yaw
        roll: a float that represents the chassis roll
        turrets: a list of tuples containing turret pitch (index 0) and yaw (index 1) in degrees.
    """

    time: int
    x_pos: float
    y_pos: float
    z_pos: float
    pitch: float
    yaw: float
    roll: float
    turrets: List[Tuple[int, float, float]]  # Turret Time, pitch, yaw;

    @staticmethod
    def get_type_id() -> int:
        """
        Returns this message's type ID, 0x0001.
        """
        return 0x0001

    @classmethod
    def parse(cls, data: bytes) -> "OdometryMessage":
        """
        Method that parses a byte message and returns the results in a message dataclass.
        """
        # Packet format:
        # time: Int
        # x_pos: float
        # y_pos: float
        # z_pos: float
        # pitch: float
        # yaw: float
        # roll: float
        # num_turrets: int
        # turret0_time: int
        # turret0_pitch: float
        # turret0_yaw: float
        # turret1_time: int
        # turret1_pitch: float
        # turret1_yaw: float
        packet_format: str = "<L6fB"
        expected_size: int = struct.calcsize(packet_format)

        time, x_pos, y_pos, z_pos, pitch, yaw, roll, num_turrets = struct.unpack(
            packet_format, data[:expected_size]
        )

        packet_format_turrets: str = "<L2f"  # Turret timestamp, pitch, yaw.
        turret_data_size: int = struct.calcsize(packet_format_turrets)
        received_turret_num: int = len(data[expected_size:]) // turret_data_size

        if (len(data[expected_size:]) // turret_data_size) != num_turrets:
            raise ValueError(f"expected {num_turrets} turrets, received {received_turret_num}")
        if len(data) != (expected_size + turret_data_size * num_turrets):
            raise ValueError(
                f"length of data must be {expected_size + turret_data_size * num_turrets}, "
                + f"received {len(data)}"
            )

        turrets_tuple_iterator: Iterator[Tuple[int, float, float]] = struct.iter_unpack(
            packet_format_turrets, data[expected_size:]
        )

        turrets_list: List[Tuple[int, float, float]] = list(turrets_tuple_iterator)

        return OdometryMessage(time, x_pos, y_pos, z_pos, pitch, yaw, roll, turrets_list)
