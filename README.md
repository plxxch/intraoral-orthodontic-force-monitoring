# Intraoral Orthodontic Force Monitoring — Sensor Firmware and Reader

Firmware for the battery-free, wireless intraoral orthodontic force sensing
system (BWS) described in:

> P. Li, L. Zhu, Y. Ding, Z. Long, Y. Yang, J. Pan, M. Gu, W. Wang, and
> Z. Yang, “RF energy harvesting for intraoral orthodontic force monitoring,”
> *Nano Energy*, vol. 121, Art. no. 109244, 2024.
> DOI: [10.1016/j.nanoen.2023.109244](https://doi.org/10.1016/j.nanoen.2023.109244)

## Overview

The BWS is a flexible, battery-free sensor that is powered and read by a
commercial UHF RFID reader. This repository contains both the **sensor
firmware** and the **reader software** used in the prototype (ST25RU3993
STUHFL reader, live force plot, Arduino/phyphox display and validation
scripts).

| Component | Part |
|---|---|
| Microcontroller | TI MSP430FR2433 |
| Instrumentation amplifier | TI INA333 |
| RFID chip | Impinj Monza X-8k |
| Strain gauge | HOKURIKU HFD-20 N-A01 |
| Power management | TPS7A0520 LDO + RF rectifier (external to this firmware) |

## Firmware behaviour

1. The microcontroller wakes when the harvested supply is available.
2. It enables the instrumentation amplifier (P2.7) and the bridge supply
   (P2.6) through GPIO pins.
3. After a settling delay, it samples the amplified strain-gauge signal with
   the **10-bit ADC**.
4. The 16-bit ADC result is written to the Monza X-8k memory bank through
   **I2C** (device address `0x6E`).
5. The controller returns to low-power mode until the next activation.

The I2C access is implemented directly with the MSP430 eUSCI_B0 registers;
no Impinj MonzaX API library is required or included.

## Repository layout

```
.
├── MONZAX-dsgba.c          # sensor firmware (main)
├── pre_init.cpp            # TI C startup hook (BSD)
├── lnk_msp430fr2433.cmd    # TI linker command file (BSD)
├── targetConfigs/          # CCS target configuration
├── .cproject / .project    # CCS project metadata
├── reader/                 # ST25RU3993 reader, Arduino bridge, validation
│   ├── bwofss_reader.py
│   ├── stuhfl_common.py
│   ├── modbus_rtu.py
│   ├── arduino/Phyphon_orthodontic.ino
│   └── validation/
├── THIRD_PARTY_NOTICES.md
├── CITATION.cff
└── LICENSE
```

## Building

1. Install **Code Composer Studio 8.3.0** with MSP430 support.
2. `File → Import → CCS Projects` and select this folder.
3. Select the **MSP430FR2433** target.
4. Build and flash with an MSP-FET / eZ430 probe, or use the Spy-Bi-Wire
   interface of the BWS board.

No external files need to be downloaded for the sensor: the only third-party
source files are TI's BSD-licensed startup hook and linker command file.

## Reader

The reader uses an **ST25RU3993** UHF RFID evaluation board to read the Monza
X-8k tag in the BWS. It reads 8 bytes from the EPC memory bank, takes the
16-bit ADC value from bytes 4–5, subtracts a no-load zero point and converts to
force with the paper's `50.04` counts/N factor. It also provides:

- a live PyQtGraph force plot;
- CSV logging;
- an Arduino/phyphox BLE bridge for displaying force on a phone;
- validation scripts for a commercial force meter and a temperature/humidity
  sensor.

The ST25RU3993 STUHFL SDK v3.0.2.0 is **not** bundled. See
[reader/README.md](reader/README.md) for hardware, SDK/wrapper setup,
calibration and run instructions.

## License

The MIT license in [LICENSE](LICENSE) covers the original firmware and reader
code authored by Pengyu Li. Third-party files remain under their own licenses —
see [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md).

## Citation

```bibtex
@article{li2024orthodontic,
  author  = {Li, Pengyu and Zhu, Luying and Ding, Yongtao and Long, Zhihe and Yang, Yanqi and Pan, Jia and Gu, Min and Wang, Wenping and Yang, Zhengbao},
  title   = {RF energy harvesting for intraoral orthodontic force monitoring},
  journal = {Nano Energy},
  volume  = {121},
  pages   = {109244},
  year    = {2024},
  doi     = {10.1016/j.nanoen.2023.109244}
}
```
