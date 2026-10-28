"""
Shared helpers for the ST25RU3993 / STUHFL orthodontic force reader.

The ST25RU3993 STUHFL SDK is NOT bundled with this repository. Install the
SDK v3.0.2.0 separately and point ``STUHFL_WRAPPER`` (or ``--wrapper``) at
``.../Middleware/wrapper/python``. The script then imports STUHFL from there.

Copyright (c) 2024 Pengyu Li
SPDX-License-Identifier: MIT
"""

import os
import sys


def load_stuhfl(wrapper_path=None):
    """Import the STUHFL Python wrapper, optionally from an explicit path."""
    wrapper_path = wrapper_path or os.environ.get("STUHFL_WRAPPER")
    if wrapper_path:
        wrapper_path = os.path.abspath(os.path.expanduser(wrapper_path))
        if not os.path.isdir(wrapper_path):
            raise RuntimeError(
                "STUHFL wrapper directory not found: {}".format(wrapper_path)
            )
        os.environ["PATH"] = wrapper_path + os.pathsep + os.environ.get("PATH", "")
        if hasattr(os, "add_dll_directory"):
            try:
                os.add_dll_directory(wrapper_path)
            except OSError:
                pass
        if wrapper_path not in sys.path:
            sys.path.insert(0, wrapper_path)

    try:
        import STUHFL
    except ImportError as exc:
        raise RuntimeError(
            "Cannot import STUHFL. Install the ST25RU3993 STUHFL SDK v3.0.2.0 "
            "and set STUHFL_WRAPPER to its Middleware/wrapper/python directory."
        ) from exc

    return STUHFL


def serial_port_candidates():
    """Return serial ports to probe for the reader."""
    try:
        from serial.tools import list_ports

        ports = [p.device for p in list_ports.comports()]
        if ports:
            return ports
    except Exception:
        pass

    if os.name == "nt":
        return ["COM{}".format(i) for i in range(1, 257)]

    import glob

    return sorted(glob.glob("/dev/tty*"))


def connect_reader(stuhfl, port=None):
    """Connect to the first ST25RU3993 reader that answers, return its port."""
    candidates = [port] if port else serial_port_candidates()

    for candidate in candidates:
        try:
            if stuhfl.Connect(candidate) == 0:
                board_version = stuhfl.STUHFL_T_VersionBoard()
                if board_version.fetch() == stuhfl.STUHFL_ERR_NONE:
                    return candidate
                stuhfl.Disconnect()
        except OSError:
            pass

    raise RuntimeError(
        "No ST25RU3993 reader found. Check the USB connection or pass --reader-port."
    )


def configure_reader(stuhfl, antenna=1):
    """Apply the Gen2/UHF settings used by the prototype."""
    antenna_id = (
        stuhfl.STUHFL_D_ANTENNA_1 if antenna == 1 else stuhfl.STUHFL_D_ANTENNA_2
    )

    tx_rx = stuhfl.STUHFL_T_ST25RU3993_TxRxCfg()
    tx_rx.fetch()
    tx_rx.rxSensitivity = 3
    tx_rx.txOutputLevel = 0
    tx_rx.usedAntenna = antenna_id
    tx_rx.alternateAntennaInterval = 1
    tx_rx.commit()

    inventory_cfg = stuhfl.STUHFL_T_ST25RU3993_Gen2_InventoryCfg()
    inventory_cfg.fetch()
    inventory_cfg.inventoryOption.fast = True
    inventory_cfg.inventoryOption.autoAck = False
    inventory_cfg.antiCollision.startQ = 4
    inventory_cfg.antiCollision.adaptiveQ = True
    inventory_cfg.adaptiveSensitivity.enable = True
    inventory_cfg.queryParams.toggleTarget = True
    inventory_cfg.queryParams.targetDepletionMode = True
    inventory_cfg.commit()

    protocol_cfg = stuhfl.STUHFL_T_ST25RU3993_Gen2_ProtocolCfg()
    protocol_cfg.fetch()
    protocol_cfg.tari = stuhfl.STUHFL_D_GEN2_TARI_25_00
    protocol_cfg.blf = stuhfl.STUHFL_D_GEN2_BLF_256
    protocol_cfg.coding = stuhfl.STUHFL_D_GEN2_CODING_MILLER8
    protocol_cfg.trext = stuhfl.STUHFL_D_TREXT_ON
    protocol_cfg.commit()

    lbt = stuhfl.STUHFL_T_ST25RU3993_FreqLBT()
    lbt.fetch()
    lbt.listeningTime = 0
    lbt.idleTime = 0
    lbt.rssiLogThreshold = 38
    lbt.skipLBTcheck = True
    lbt.commit()

    channel_list = stuhfl.STUHFL_T_ST25RU3993_ChannelList(
        stuhfl.STUHFL_D_PROFILE_USA
    )
    channel_list.antenna = antenna_id
    channel_list.persistent = False
    channel_list.channelListIdx = 0
    channel_list.commit()

    freq_hop = stuhfl.STUHFL_T_ST25RU3993_FreqHop()
    freq_hop.maxSendingTime = 400
    freq_hop.minSendingTime = 400
    freq_hop.mode = stuhfl.STUHFL_D_FREQUENCY_HOP_MODE_IGNORE_MIN
    freq_hop.commit()

    select = stuhfl.STUHFL_T_Gen2_Select()
    select.mode = stuhfl.STUHFL_D_GEN2_SELECT_MODE_CLEAR_LIST
    select.execute()


def read_adc(stuhfl):
    """Read the 8-byte EPC bank and return the 16-bit ADC value (bytes 4-5)."""
    inventory = stuhfl.STUHFL_T_Gen2_Inventory()
    inventory.rssiMode = stuhfl.STUHFL_D_RSSI_MODE_SECOND_BYTE
    inventory.inventoryDelay = 0

    if inventory.execute() != stuhfl.STUHFL_ERR_NONE:
        return None
    if len(inventory.tagList) == 0:
        return None

    epc = inventory.tagList[0].epc

    select = stuhfl.STUHFL_T_Gen2_Select()
    select.mode = stuhfl.STUHFL_D_GEN2_SELECT_MODE_CLEAR_AND_ADD
    select.target = stuhfl.STUHFL_D_GEN2_SELECT_TARGET_SL
    select.action = 0
    select.memoryBank = stuhfl.STUHFL_D_GEN2_MEMORY_BANK_EPC
    select.maskBitPointer = 0x00000020
    select.mask = epc
    select.maskBitLength = len(epc) * 8
    select.truncation = False
    select.execute()

    read_data = stuhfl.STUHFL_T_Gen2_Read()
    read_data.memoryBank = stuhfl.STUHFL_D_GEN2_MEMORY_BANK_EPC
    read_data.wordPtr = 0
    read_data.numBytesToRead = 8
    read_data.pwd = [0] * stuhfl.STUHFL_D_PASSWORD_LEN

    if read_data.execute() != stuhfl.STUHFL_ERR_NONE:
        return None

    data = list(read_data.data)
    if len(data) < 6:
        return None

    return (data[4] << 8) | data[5]


def disconnect_reader(stuhfl):
    """Disconnect from the reader, ignoring errors during shutdown."""
    try:
        stuhfl.Disconnect()
    except Exception:
        pass
