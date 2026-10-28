"""
Minimal Modbus RTU helpers for the force-meter and temperature/humidity
validation sensors.

Both sensors are read with function code 0x03 (read holding registers):
    request:  slave 0x03 start_hi start_lo count_hi count_lo crc_lo crc_hi
The force meter returns two registers holding an IEEE-754 float; the
temperature/humidity sensor returns humidity and temperature as 16-bit
values scaled by 0.1.

Copyright (c) 2024 Pengyu Li
SPDX-License-Identifier: MIT
"""

import struct
import time


def crc16(data):
    """Modbus CRC-16 (poly 0xA001), returned as an integer."""
    crc = 0xFFFF
    for byte in data:
        crc ^= byte
        for _ in range(8):
            if crc & 0x0001:
                crc = (crc >> 1) ^ 0xA001
            else:
                crc >>= 1
    return crc & 0xFFFF


def read_holding_registers(serial_port, slave=1, start=0, count=2, timeout=1.0):
    """Read ``count`` holding registers; return the data bytes or None."""
    frame = bytes(
        [
            slave,
            0x03,
            (start >> 8) & 0xFF,
            start & 0xFF,
            (count >> 8) & 0xFF,
            count & 0xFF,
        ]
    )
    crc = crc16(frame)
    frame += bytes([crc & 0xFF, (crc >> 8) & 0xFF])

    serial_port.reset_input_buffer()
    serial_port.write(frame)

    expected = 5 + 2 * count
    data = b""
    deadline = time.time() + timeout
    while len(data) < expected and time.time() < deadline:
        data += serial_port.read(expected - len(data))

    if len(data) != expected:
        return None
    if data[0] != slave or data[1] != 0x03 or data[2] != 2 * count:
        return None

    crc_calc = crc16(data[:-2])
    if data[-2] != (crc_calc & 0xFF) or data[-1] != ((crc_calc >> 8) & 0xFF):
        return None

    return data[3:-2]


def decode_float32(data):
    """Decode two Modbus registers as a big-endian IEEE-754 float."""
    if data is None or len(data) < 4:
        return None
    return struct.unpack(">f", bytes(data[:4]))[0]


def decode_u16(data, offset=0):
    """Decode a big-endian unsigned 16-bit value from a byte sequence."""
    if data is None or len(data) < offset + 2:
        return None
    return (data[offset] << 8) | data[offset + 1]
