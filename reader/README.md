# BWOFSS Orthodontic Force Reader

Reader software for the battery-free, wireless intraoral orthodontic force
sensing system (BWS) in the companion paper:

> P. Li, L. Zhu, Y. Ding, Z. Long, Y. Yang, J. Pan, M. Gu, W. Wang, and
> Z. Yang, “RF energy harvesting for intraoral orthodontic force monitoring,”
> *Nano Energy*, vol. 121, Art. no. 109244, 2024.
> DOI: [10.1016/j.nanoen.2023.109244](https://doi.org/10.1016/j.nanoen.2023.109244)

The reader uses an **ST25RU3993** UHF RFID evaluation board to read the Monza
X-8k RFID chip in the BWS sensor, converts the ADC value to force, plots it in
real time, and can optionally forward it to an Arduino/phyphox bridge for
display on a phone.

## Hardware

| Part | Role |
|---|---|
| ST25RU3993 UHF RFID reader board | Reads the sensor tag (USB serial) |
| UHF antenna | Connected to the reader |
| Impinj Monza X-8k | RFID chip in the BWS sensor |
| BLE-capable Arduino (optional) | Receives force values over USB serial and forwards them to phyphox |

The reader uses the **USA frequency profile** (902–928 MHz, the 915 MHz band
used in the paper).

## Data mapping

The sensor firmware writes the 16-bit ADC value to the Monza X-8k memory bank
through I2C. The reader inventories the tag, selects it, and reads **8 bytes
from the EPC memory bank at word pointer 0**:

```
byte 0..3  EPC/PC/CRC fields as returned by the tag
byte 4..5  16-bit ADC value written by the sensor
```

The reader computes:

```
ADC = (data[4] << 8) | data[5]
force [N] = (ADC - zeropoint) / 50.04
```

The no-load zero point is measured at start-up by averaging
`--zero-samples` readings. The 50.04 counts/N factor is the calibration used in
the paper.

## Software requirements

- Python 3.8+
- A local installation of the **ST25RU3993 STUHFL SDK v3.0.2.0**
  (not included in this repository).
- The SDK's Python wrapper at
  `.../Middleware/wrapper/python`. Point `STUHFL_WRAPPER` at that directory, or
  pass `--wrapper`.
- Python packages:

```bash
pip install -r requirements.txt
```

`pyqtgraph`/`PyQt5` are only needed for the live plot; `--no-plot` works
without a display.

## Running the reader

```bash
export STUHFL_WRAPPER=/path/to/ST25RU3993_STUHFL_SDK/Middleware/wrapper/python

# Live plot, auto-detect the reader port, record to CSV
python bwofss_reader.py --csv force.csv

# Explicit reader port, 5-sample average, no plot
python bwofss_reader.py --reader-port COM4 --samples 5 --no-plot --count 100 --csv force.csv

# Forward each force value to an Arduino/phyphox bridge
python bwofss_reader.py --serial-port COM8 --serial-baud 115200
```

Useful options:

| Option | Meaning |
|---|---|
| `--reader-port` | ST25RU3993 serial port (default: probe all ports) |
| `--wrapper` | STUHFL Python wrapper directory (overrides `STUHFL_WRAPPER`) |
| `--zero` | known no-load ADC value; skips calibration |
| `--zero-samples` | samples averaged for the zero point (default 3) |
| `--samples` | ADC samples averaged per reading (default 3) |
| `--scale` | ADC counts per newton (default 50.04) |
| `--interval-ms` | plot/read interval (default 200 ms) |
| `--count` | number of readings, 0 = infinite |
| `--csv` | write `timestamp,adc,force_n` |
| `--serial-port` / `--serial-baud` | downstream Arduino port and baud (default 115200) |
| `--no-plot` | headless text output |

## Phone display (Arduino + phyphox)

`arduino/Phyphon_orthodontic.ino` reads the force lines sent by the reader and
forwards them over BLE to the **phyphox** app, where the experiment
“Orthodontic Force Monitor” plots force in newtons.

1. Install the **phyphoxBle** library in the Arduino IDE.
2. Flash the sketch to a BLE-capable board (e.g. Arduino Nano 33 BLE/IoT).
3. Connect the board to the PC; pass its port to the reader:

```bash
python bwofss_reader.py --serial-port COM8 --serial-baud 115200
```

The reader sends one `force\n` line per sample; the Arduino forwards each value
with `PhyphoxBLE::write()`.

## Validation scripts

`validation/` contains two acquisition scripts used to characterize and
validate the sensor. Both record the RFID ADC alongside a reference sensor to
CSV.

### Commercial force meter

```bash
python validation/force_meter_validation.py \
    --force-port COM11 --csv force_validation.csv
```

The force meter uses Modbus RTU at **9600 8N1**, slave 1, function 0x03,
start register 0, two registers. The request is `01 03 00 00 00 02 C4 0B`; the
four response data bytes are decoded as a big-endian IEEE-754 float.

### Temperature / humidity sensor

```bash
python validation/temperature_validation.py \
    --sensor-port COM11 --csv temperature_validation.csv
```

The temperature/humidity sensor uses the same Modbus request. Register 0 is
humidity × 0.1 %RH and register 1 is temperature × 0.1 °C.

Both validation scripts use `stuhfl_common.py` to read the RFID tag, and
`modbus_rtu.py` for the Modbus request/CRC/decoding.

## Files

```
reader/
├── bwofss_reader.py                  # main reader (calibration, plot, CSV, serial)
├── stuhfl_common.py                  # STUHFL connection/configuration/tag read
├── modbus_rtu.py                     # Modbus RTU helpers
├── requirements.txt
├── validation/
│   ├── force_meter_validation.py
│   └── temperature_validation.py
└── arduino/
    └── Phyphon_orthodontic.ino
```

## Notes and limitations

- The ST SDK's automatic antenna-tuning routine is not invoked here. The
  channel list and Gen2 settings match the prototype; if the antenna needs
  re-tuning, run the ST demo once or call its tuning routine.
- The reader uses EPC bank bytes 4–5. Confirm this mapping if the sensor
  firmware's RFID memory address changes.
- `force = (ADC - zero) / 50.04` is the paper's single-point calibration. For a
  different sensor batch, re-measure the zero point and, if needed, re-fit the
  scale factor using `force_meter_validation.py`.
- The Arduino/phyphox path requires a BLE board and the `phyphoxBle` library;
  baud rate and serial port are configurable.

## License

The MIT license in the repository root covers the original reader and Arduino
code authored by Pengyu Li. The ST25RU3993 STUHFL SDK is **not** included and
remains under ST's SLA0052 license; the `phyphoxBle` library and Python
dependencies remain under their own licenses. See
[../THIRD_PARTY_NOTICES.md](../THIRD_PARTY_NOTICES.md).
