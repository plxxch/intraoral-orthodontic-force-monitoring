#!/usr/bin/env python3
"""
Validation: record the RFID force sensor and a Modbus temperature/humidity
sensor simultaneously. Used to check temperature drift / compensation.

The temperature/humidity sensor uses the same Modbus request as the force
meter (9600 8N1, slave 1, function 0x03, two registers):
    request: 01 03 00 00 00 02 C4 0B
    register 0 = humidity x 0.1 %RH
    register 1 = temperature x 0.1 degC

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

from modbus_rtu import decode_u16, read_holding_registers
from stuhfl_common import (
    configure_reader,
    connect_reader,
    disconnect_reader,
    load_stuhfl,
    read_adc,
)


def parse_args():
    parser = argparse.ArgumentParser(
        description="Record RFID ADC and a Modbus temperature/humidity sensor."
    )
    parser.add_argument("--sensor-port", required=True, help="temperature sensor serial port")
    parser.add_argument("--sensor-baud", type=int, default=9600)
    parser.add_argument("--sensor-slave", type=int, default=1)
    parser.add_argument("--reader-port", help="ST25RU3993 serial port (default: auto)")
    parser.add_argument("--wrapper", help="STUHFL Python wrapper directory")
    parser.add_argument("--antenna", type=int, choices=(1, 2), default=1)
    parser.add_argument("--samples", type=int, default=1, help="ADC samples averaged per row")
    parser.add_argument("--interval-ms", type=int, default=1000)
    parser.add_argument("--count", type=int, default=0, help="rows to record, 0 = infinite")
    parser.add_argument("--csv", default="temperature_validation.csv")
    return parser.parse_args()


def read_temperature(port, slave):
    for _ in range(3):
        try:
            data = read_holding_registers(port, slave=slave, start=0, count=2)
        except (serial.SerialException, OSError):
            data = None
        if data is not None:
            humidity = decode_u16(data, 0)
            temperature = decode_u16(data, 2)
            if humidity is not None and temperature is not None:
                return temperature * 0.1, humidity * 0.1
        time.sleep(0.05)
    return None


def main():
    args = parse_args()

    stuhfl = load_stuhfl(args.wrapper)
    reader_port = connect_reader(stuhfl, args.reader_port)
    print("Connected to ST25RU3993 reader on {}".format(reader_port))
    configure_reader(stuhfl, args.antenna)

    sensor = serial.Serial(args.sensor_port, args.sensor_baud, timeout=1)
    directory = os.path.dirname(os.path.abspath(args.csv))
    if directory:
        os.makedirs(directory, exist_ok=True)
    handle = open(args.csv, "w", newline="", encoding="utf-8")
    writer = csv.writer(handle)
    writer.writerow(["timestamp", "adc", "temperature_c", "humidity_pct"])

    print("Recording RFID ADC and temperature/humidity to {}".format(args.csv))
    count = 0

    try:
        while args.count == 0 or count < args.count:
            adc_values = []
            for _ in range(max(1, args.samples)):
                adc = read_adc(stuhfl)
                if adc is not None:
                    adc_values.append(adc)
                time.sleep(0.1)

            reading = read_temperature(sensor, args.sensor_slave)

            if adc_values and reading is not None:
                adc = float(np.mean(adc_values))
                temperature, humidity = reading
                writer.writerow(
                    [
                        datetime.now().isoformat(timespec="seconds"),
                        "{:.1f}".format(adc),
                        "{:.2f}".format(temperature),
                        "{:.2f}".format(humidity),
                    ]
                )
                handle.flush()
                print(
                    "adc={:.1f}  T={:.2f} C  RH={:.2f} %".format(
                        adc, temperature, humidity
                    )
                )
                count += 1
            else:
                print("Missing RFID or temperature sample; retrying...")

            time.sleep(max(0.0, args.interval_ms / 1000.0))
    except KeyboardInterrupt:
        print("\nStopped by user")
    finally:
        handle.close()
        sensor.close()
        disconnect_reader(stuhfl)


if __name__ == "__main__":
    main()
