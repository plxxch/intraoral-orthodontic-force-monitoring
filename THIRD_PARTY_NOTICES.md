# Third-party notices

The MIT license in [LICENSE](LICENSE) applies only to the original firmware and
reader code authored by Pengyu Li. Third-party files remain under their own
licenses; their copyright notices and license texts are retained in the file
headers.

## Included

| File | Copyright | License |
|---|---|---|
| `pre_init.cpp` | © 2015 Texas Instruments Incorporated | BSD 3-Clause |
| `lnk_msp430fr2433.cmd` | © 2018 Texas Instruments Incorporated | BSD 3-Clause |

`targetConfigs/MSP430FR2433.ccxml` and `targetConfigs/readme.txt` are generated
by Code Composer Studio and carry no separate license header.

The BSD 3-Clause text is reproduced in the files above: redistribution is
permitted provided the copyright notice, conditions and disclaimer are
retained, and TI's name is not used to endorse derived products without written
permission. The software is provided “AS IS”, without warranty.

## Reader dependencies (not included)

The reader uses the **ST25RU3993 STUHFL SDK v3.0.2.0**, which is distributed by
STMicroelectronics under its **SLA0052 Rev3** software package license. That
license permits redistribution of source and binary forms only if the copyright
notice, conditions and disclaimer are retained, requires the software to be
used with ST ICs (NFC/UHF reader), and forbids relicensing it under open-source
terms. The SDK is therefore **not** part of this MIT-licensed repository;
install it separately and accept ST's terms.

The ST SDK's Python demo, wrapper and firmware files are not redistributed
here. The scripts in `reader/` are original MIT-licensed code written against
the STUHFL public API. The SDK's `Middleware/wrapper/python` directory must be
available at run time (for example through `STUHFL_WRAPPER`); its files remain
under SLA0052.

The Arduino sketch uses the **phyphoxBle** library, which is not included.
Install it through the Arduino Library Manager; it remains under its own
license.

The Python dependencies (`numpy`, `pyserial`, `pyqtgraph`, `PyQt5`) are not
bundled and remain under their respective licenses.

## Not included

No Impinj MonzaX API library is included. The I2C access to the Monza X-8k is
implemented directly with the MSP430 eUSCI_B0 registers in
`MONZAX-dsgba.c`. The device header `MSP430FR2433.h` is supplied by Code
Composer Studio and is not part of this repository.

## Trademarks

MSP430 and Code Composer Studio are trademarks or registered trademarks of
Texas Instruments Incorporated. Monza is a trademark of Impinj, Inc.
ST25RU3993 and STUHFL are trademarks of STMicroelectronics. phyphox is a
project/trademark of RWTH Aachen University. All other trademarks are the
property of their respective owners.
