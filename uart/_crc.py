from typing import List

"""
This file defines two CRC functions calculated with lookup tables: CRC8/MAXIM-DOW and CRC16/MCRF4XX.
Polynomials (reflected) are 0x8c and 0x8408. Both have initial shift register values as arguments,
however they default to -1.
"""


def compute_table(poly: int) -> List[int]:
    """
    Method to compute tables above.

    Args:
        poly: Polynomial (reversed) used to compute table.
    Returns:
        List of length 256 containing division remainders for all possible single bytes.
    """
    crc = 0x1
    table = [0] * 256
    for i in reversed(range(8)):
        if crc & 0x1:
            crc = (crc >> 1) ^ poly
        else:
            crc = crc >> 1
        for j in range(0, 255, 2 ** (i + 1)):
            table[(2 ** i) + j] = crc ^ table[j]

    return table


# CRC lookup tables
CRC8_TABLE = compute_table(0x8C)
CRC16_TABLE = compute_table(0x8408)


def crc8(data: bytes, crc_init: int = 0xFF) -> int:
    """
    Calculate CRC-8/MAXIM-DOW using the given table.

    Args:
        data: Bytes to be hashed
        crc_init: Initial value
    Returns:
        Calculated value of CRC
    """
    checksum = crc_init
    for byte in data:
        checksum = CRC8_TABLE[checksum ^ byte]
    return checksum


def crc16(data: bytes, init_crc: int = 0xFFFF) -> int:
    """
    Calculate CRC-16/MCRF4XX using the given table.

    Args:
        data: Data to be hashed, must be int
        init_crc: Initial CRC value
    Returns:
         Calculated value of CRC
    """
    checksum = init_crc
    for byte in data:
        checksum = (checksum >> 8) ^ CRC16_TABLE[(checksum ^ byte) & 0xFF]
    return checksum & 0xFFFF
