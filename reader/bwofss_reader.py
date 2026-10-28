#!/usr/bin/env python3
"""
BWOFSS — battery-free wireless orthodontic force sensor reader.

Connects to an ST25RU3993 UHF RFID reader, reads the 16-bit ADC value that the
BWS sensor writes to the Monza X-8k EPC memory bank (bytes 4-5), converts it
to force using a no-load zero point, and displays/records the result.

The ST25RU3993 STUHFL SDK is not bundled. Install SDK v3.0.2.0 and point
STUHFL_WRAPPER (or --wrapper) at .../Middleware/wrapper/python.

Force conversion follows the paper's calibration:
    force [N] = (ADC - zeropoint) / 50.04

Copyright (c) 2024 Pengyu Li
SPDX-License-Identifier: MIT
"""

import argparse
import csv
import os
import time
from datetime import datetime

import numpy as np
import serial

from stuhfl_common import (
    configure_reader,
    connect_reader,
    disconnect_reader,
    load_stuhfl,
    read_adc,
)

DEFAULT_FORCE_SCALE = 50.04


def parse_args():
    parser = argparse.ArgumentParser(
        description="Read the BWOFSS orthodontic force sensor via ST25RU3993."
    )
    parser.add_argument("--reader-port", help="reader serial port (default: auto-detect)")
    parser.add_argument(
        "--wrapper",
        help="STUHFL Python wrapper directory (default: $STUHFL_WRAPPER)",
    )
    parser.add_argument("--antenna", type=int, choices=(1, 2), default=1)
    parser.add_argument(
        "--scale",
        type=float,
        default=DEFAULT_FORCE_SCALE,
        help="ADC counts per newton (default: 50.04)",
    )
    parser.add_argument(
        "--zero",
        type=float,
        help="known no-load ADC zero point; skip the calibration step",
    )
    parser.add_argument("--zero-samples", type=int, default=3)
    parser.add_argument("--samples", type=int, default=3, help="ADC samples averaged per reading")
    parser.add_argument("--interval-ms", type=int, default=200)
    parser.add_argument("--count", type=int, default=0, help="number of samples, 0 = infinite")
    parser.add_argument("--history", type=int, default=200, help="points kept in the live plot")
    parser.add_argument("--csv", help="write timestamp,adc,force_n to this CSV file")
    parser.add_argument("--serial-port", help="optional downstream serial port (Arduino/phyphox)")
    parser.add_argument("--serial-baud", type=int, default=115200)
    parser.add_argument("--no-plot", action="store_true", help="headless text output")
    return parser.parse_args()


def open_csv(path):
    directory = os.path.dirname(os.path.abspath(path))
    if directory:
        os.makedirs(directory, exist_ok=True)
    handle = open(path, "w", newline="", encoding="utf-8")
    writer = csv.writer(handle)
    writer.writerow(["timestamp", "adc", "force_n"])
    return handle, writer


class ForceReader:
    def __init__(self, stuhfl, zero_point, scale, samples):
        self.stuhfl = stuhfl
        self.zero_point = zero_point
        self.scale = scale
        self.samples = max(1, samples)

    def calibrate(self, samples):
        values = []
        for _ in range(max(1, samples)):
            adc = read_adc(self.stuhfl)
            if adc is not None:
                values.append(adc)
            time.sleep(0.1)
        if not values:
            raise RuntimeError("Calibration failed: no tag reading")
        self.zero_point = float(np.mean(values))
        return self.zero_point

    def read(self):
        values = []
        for _ in range(self.samples):
            adc = read_adc(self.stuhfl)
            if adc is not None:
                values.append(adc)
            time.sleep(0.1)
        if not values:
            return None
        adc = float(np.mean(values))
        force = (adc - self.zero_point) / self.scale
        return force, adc


def record_sample(writer, downstream, force, adc):
    timestamp = datetime.now().isoformat(timespec="seconds")
    if writer is not None:
        writer.writerow([timestamp, "{:.1f}".format(adc), "{:.4f}".format(force)])
    if downstream is not None:
        downstream.write("{:.4f}\n".format(force).encode("ascii"))
    print("{}  adc={:.1f}  force={:.3f} N".format(timestamp, adc, force))


def run_headless(reader, args, writer, downstream):
    count = 0
    while args.count == 0 or count < args.count:
        result = reader.read()
        if result is None:
            print("No tag reading; retrying...")
        else:
            force, adc = result
            record_sample(writer, downstream, force, adc)
            count += 1
        time.sleep(max(0.0, args.interval_ms / 1000.0))


def run_plot(reader, args, writer, downstream):
    import pyqtgraph as pg
    from pyqtgraph.Qt import QtCore, QtGui

    pg.setConfigOptions(background="w", foreground="k")
    app = pg.mkQApp()

    window = QtGui.QWidget()
    window.setWindowTitle("Battery-free wireless orthodontic force sensor")
    window.resize(1000, 700)
    layout = QtGui.QGridLayout(window)

    plot = pg.PlotWidget()
    layout.addWidget(plot)
    plot.setTitle("Battery-free wireless orthodontic force sensor")
    plot.setLabel("left", "Force", units="N")
    plot.setLabel("bottom", "Sample")
    plot.showGrid(x=True, y=True)
    plot.setYRange(-1, 5)

    curve = plot.plot(pen=pg.mkPen(width=3, color="r"))
    history = []

    def update():
        result = reader.read()
        if result is None:
            return
        force, adc = result
        history.append(force)
        if len(history) > args.history:
            del history[0]
        curve.setData(history)
        record_sample(writer, downstream, force, adc)

    timer = QtCore.QTimer()
    timer.timeout.connect(update)
    timer.start(max(50, args.interval_ms))

    window.show()
    app.exec_()


def main():
    args = parse_args()

    stuhfl = load_stuhfl(args.wrapper)
    port = connect_reader(stuhfl, args.reader_port)
    print("Connected to ST25RU3993 reader on {}".format(port))
    configure_reader(stuhfl, args.antenna)

    reader = ForceReader(stuhfl, 0.0, args.scale, args.samples)
    if args.zero is not None:
        reader.zero_point = args.zero
    else:
        zero = reader.calibrate(args.zero_samples)
        print("Calibrated zero point: {:.1f} ADC".format(zero))

    csv_handle = None
    writer = None
    downstream = None

    try:
        if args.csv:
            csv_handle, writer = open_csv(args.csv)
        if args.serial_port:
            downstream = serial.Serial(
                args.serial_port, args.serial_baud, timeout=1
            )

        if args.no_plot:
            run_headless(reader, args, writer, downstream)
        else:
            run_plot(reader, args, writer, downstream)
    except KeyboardInterrupt:
        print("\nStopped by user")
    finally:
        if downstream is not None:
            downstream.close()
        if csv_handle is not None:
            csv_handle.close()
        disconnect_reader(stuhfl)


if __name__ == "__main__":
    main()
