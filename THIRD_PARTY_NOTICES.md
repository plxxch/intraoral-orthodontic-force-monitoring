# Third-party notices

The MIT license in [LICENSE](LICENSE) applies only to the original firmware
authored by Pengyu Li. Third-party files remain under their own licenses; their
copyright notices and license texts are retained in the file headers.

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

## Not included

No Impinj MonzaX API library is included. The I2C access to the Monza X-8k is
implemented directly with the MSP430 eUSCI_B0 registers in
`MONZAX-dsgba.c`. The device header `MSP430FR2433.h` is supplied by Code
Composer Studio and is not part of this repository.

## Trademarks

MSP430 and Code Composer Studio are trademarks or registered trademarks of
Texas Instruments Incorporated. Monza is a trademark of Impinj, Inc. All other
trademarks are the property of their respective owners.
