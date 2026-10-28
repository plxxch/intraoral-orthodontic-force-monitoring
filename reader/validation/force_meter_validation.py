#!/usr/bin/env python3
"""
Validation: record the RFID force sensor and a commercial Modbus force meter
simultaneously. Used to calibrate / validate the (ADC - zero) / 50.04 mapping.

Force meter wiring used in the prototype:
    9600 8N1, slave 1, function 0x03, start register 0, 2 registers
    request: 01 03 00 00 00 02 C4 0B
    response data bytes [3:7] = big-endian IEEE-754 float

Copyright (c) 2024 Pengyu Li
SPDX-License-Identifier: MIT
"""

import argparse
import csv
import os
import sys
import time
from datetime import datetime

import numpy as np
import serial

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from modbus_rtu import decode_float32, read_holding_registers
from stuhfl_common import (
    configure_reader,
    connect_reader,
    disconnect_reader,
    load_stuhfl,
    read_adc,
)


def parse_args():
    parser = argparse.ArgumentParser(
        description="Record RFID ADC and a Modbus force meter to CSV."
    )
    parser.add_argument("--force-port", required=True, help="force meter serial port")
    parser.add_argument("--force-baud", type=int, default=9600)
    parser.add_argument("--force-slave", type=int, default=1)
    parser.add_argument("--reader-port", help="ST25RU3993 serial port (default: auto)")
    parser.add_argument("--wrapper", help="STUHFL Python wrapper directory")
    parser.add_argument("--antenna", type=int, choices=(1, 2), default=1)
    parser.add_argument("--samples", type=int, default=1, help="ADC samples averaged per row")
    parser.add_argument("--interval-ms", type=int, default=1000)
    parser.add_argument("--count", type=int, default=0, help="rows to record, 0 = infinite")
    parser.add_argument("--csv", default="force_validation.csv")
    return parser.parse_args()


def read_force_meter(port, slave):
    data = read_holding_registers(port, slave=slave, start=0, count=2)
    return decode_float32(data)


def read_force(port, slave):
    for _ in range(3):
        value = read_while_available(port, slave)
        if value is not None:
            return value
        time.sleep(0.05)
    return None


def read_while_available(port, slave):
    try:
        return read_force_meter(port, slave)
    except (serial.SerialException, OSError):
        return None


def main():
    args = parse_args()

    stuhfl = load_stuhfl(args.wrapper)
    reader_port = connect_reader(stuhfl, args.reader_port)
    print("Connected to ST25RU3993 reader on {}".format(reader_port))
    configure_reader(stuhfl, args.antenna)

    meter = serial.Serial(args.force_port, args.force_baud, timeout=1)
    directory = os.path.dirname(os.path.abspath(args.csv))
    if directory:
        os.makedirs(directory, exist_ok=True)
    handle = open(args.csv, "w", newline="", encoding="utf-8")
    writer = csv.writer(handle)
    writer.writerow(["timestamp", "adc", "force_n"])

    print("Recording RFID ADC and force meter to {}".format(args.csv))
    count = 0

    try:
        while args.count == 0 or count < args.count:
            adc_values = []
            for _ in range(max(1, args.samples)):
                adc = read_adc(stuhfl)
                if adc is not None:
                    adc_values.append(adc)
                time.sleep(0.1)

            force = read_force(meter, args.force_slave)

            if adc_values and force is not None:
                adc = float(np.mean(adc_values))
                writer.writerow(
                    [
                        datetime.now().isoformat(timespec="seconds"),
                        "{:.1f}".format(adc),
                        "{:.4f}".format(force),
                    ]
                )
                handle.flush()
                print(
                    "adc={:.1f}  force_meter={:.3f} N".format(adc, force)
                )
                count += 1
            else:
                print("Missing RFID or force-meter sample; retrying...")

            time.sleep(max(0.0, args.interval_ms / 1000.0))
    except KeyboardInterrupt:
        print("\nStopped by user")
    finally:
        handle.close()
        meter.close()
        disconnect_reader(stuhfl)


if __name__ == "__main__":
    main()
