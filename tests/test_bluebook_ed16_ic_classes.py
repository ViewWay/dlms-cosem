"""Tests for Blue Book Ed.16 new IC classes - class_id verification and instantiation."""

import pytest

from dlms_cosem.cosem.obis import Obis


# Helper
LN = Obis(0, 0, 1, 0, 0, 255)

# --- Data Storage ---
from dlms_cosem.cosem.C26_UtilityTables import UtilityTables
from dlms_cosem.cosem.C66_MeasurementDataMonitoring import MeasurementDataMonitoring

# --- Access Control (AutoConnect) ---
from dlms_cosem.cosem.C29_AutoConnect import AutoConnect

# --- Modems ---
from dlms_cosem.cosem.C47_GSMDiagnostic import GSMDiagnostic
from dlms_cosem.cosem.C151_LTEMonitoring import LTEMonitoring

# --- M-Bus ---
from dlms_cosem.cosem.C25_MBusSlavePortSetup import MBusSlavePortSetup
from dlms_cosem.cosem.C73_WirelessModeQChannel import WirelessModeQChannel
from dlms_cosem.cosem.C74_MBusMasterPortSetup import MBusMasterPortSetup
from dlms_cosem.cosem.C76_DLMSMBusPortSetup import DLMSMBusPortSetup

# --- Internet ---
from dlms_cosem.cosem.C48_IPv6Setup import IPv6Setup
from dlms_cosem.cosem.C152_CoAPSetup import CoAPSetup
from dlms_cosem.cosem.C153_CoAPDiagnostic import CoAPDiagnostic

# --- S-FSK PLC ---
from dlms_cosem.cosem.C50_SFSKPhyMACSetup import SFSKPhyMACSetup
from dlms_cosem.cosem.C51_SFSKActiveInitiator import SFSKActiveInitiator
from dlms_cosem.cosem.C52_SFSKMACSyncTimeouts import SFSKMACSyncTimeouts
from dlms_cosem.cosem.C53_SFSKMACCounters import SFSKMACCounters
from dlms_cosem.cosem.C55_IEC61334LLCSetup import IEC61334LLCSetup
from dlms_cosem.cosem.C56_SFSKReportingSystemList import SFSKReportingSystemList

# --- LLC ---
from dlms_cosem.cosem.C57_LLCType1Setup import LLCType1Setup
from dlms_cosem.cosem.C58_LLCType2Setup import LLCType2Setup
from dlms_cosem.cosem.C59_LLCType3Setup import LLCType3Setup

# --- PRIME PLC ---
from dlms_cosem.cosem.C80_PRIMELLCSSCSSetup import PRIMELLCSSCSSetup
from dlms_cosem.cosem.C81_PRIMEPhysicalCounters import PRIMEPhysicalCounters
from dlms_cosem.cosem.C82_PRIMEMACSetup import PRIMEMACSetup
from dlms_cosem.cosem.C83_PRIMEMACFuncParams import PRIMEMACFuncParams
from dlms_cosem.cosem.C84_PRIMEMACCounters import PRIMEMACCounters
from dlms_cosem.cosem.C85_PRIMEMACNetworkAdmin import PRIMEMACNetworkAdmin
from dlms_cosem.cosem.C86_PRIMEAppIdentification import PRIMEAppIdentification

# --- G3-PLC ---
from dlms_cosem.cosem.C90_G3MACCounters import G3MACCounters
from dlms_cosem.cosem.C91_G3MACSetup import G3MACSetup
from dlms_cosem.cosem.C92_G36LoWPANSetup import G36LoWPANSetup
from dlms_cosem.cosem.C160_G3HybridRFCounters import G3HybridRFCounters
from dlms_cosem.cosem.C161_G3HybridRFSetup import G3HybridRFSetup
from dlms_cosem.cosem.C162_G3Hybrid6LoWPANSetup import G3Hybrid6LoWPANSetup

# --- HS-PLC ---
from dlms_cosem.cosem.C140_HSPLCMACSetup import HSPLCMACSetup
from dlms_cosem.cosem.C141_HSPLCCPASSetup import HSPLCCPASSetup
from dlms_cosem.cosem.C142_HSPLCIPSSASSetup import HSPLCIPSSASSetup
from dlms_cosem.cosem.C143_HSPLCHDLCSSASSetup import HSPLCHDLCSSASSetup

# --- ZigBee ---
from dlms_cosem.cosem.C101_ZigbeeSASStartup import ZigbeeSASStartup
from dlms_cosem.cosem.C102_ZigbeeSASJoin import ZigbeeSASJoin
from dlms_cosem.cosem.C103_ZigbeeSASAPSFragmentation import ZigbeeSASAPSFragmentation
from dlms_cosem.cosem.C104_ZigbeeNetworkControl import ZigbeeNetworkControl
from dlms_cosem.cosem.C105_ZigbeeTunnelSetup import ZigbeeTunnelSetup

# --- LPWAN ---
from dlms_cosem.cosem.C126_SCHCLPWANSetup import SCHCLPWANSetup
from dlms_cosem.cosem.C127_SCHCLPWANDiagnostic import SCHCLPWANDiagnostic
from dlms_cosem.cosem.C128_LoRaWANSetup import LoRaWANSetup
from dlms_cosem.cosem.C129_LoRaWANDiagnostic import LoRaWANDiagnostic

# --- Wi-SUN ---
from dlms_cosem.cosem.C95_WiSUNSetup import WiSUNSetup
from dlms_cosem.cosem.C96_WiSUNDiagnostic import WiSUNDiagnostic
from dlms_cosem.cosem.C97_RPLDiagnostic import RPLDiagnostic
from dlms_cosem.cosem.C98_MPLDiagnostic import MPLDiagnostic

# --- IEC 14908 ---
from dlms_cosem.cosem.C130_IEC14908Identification import IEC14908Identification
from dlms_cosem.cosem.C131_IEC14908ProtocolSetup import IEC14908ProtocolSetup
from dlms_cosem.cosem.C132_IEC14908ProtocolStatus import IEC14908ProtocolStatus
from dlms_cosem.cosem.C133_IEC14908Diagnostic import IEC14908Diagnostic

# --- Payment ---
from dlms_cosem.cosem.C115_TokenGateway import TokenGateway
from dlms_cosem.cosem.C116_IEC62055Attributes import IEC62055Attributes


# (class, expected_class_id, expected_version)
CLASS_SPECS = [
    (UtilityTables, 26, 0),
    (MeasurementDataMonitoring, 66, 0),
    (AutoConnect, 29, 2),
    (GSMDiagnostic, 47, 2),
    (LTEMonitoring, 151, 1),
    (MBusSlavePortSetup, 25, 0),
    (WirelessModeQChannel, 73, 1),
    (MBusMasterPortSetup, 74, 0),
    (DLMSMBusPortSetup, 76, 0),
    (IPv6Setup, 48, 0),
    (CoAPSetup, 152, 0),
    (CoAPDiagnostic, 153, 0),
    (SFSKPhyMACSetup, 50, 1),
    (SFSKActiveInitiator, 51, 0),
    (SFSKMACSyncTimeouts, 52, 0),
    (SFSKMACCounters, 53, 0),
    (IEC61334LLCSetup, 55, 1),
    (SFSKReportingSystemList, 56, 0),
    (LLCType1Setup, 57, 0),
    (LLCType2Setup, 58, 0),
    (LLCType3Setup, 59, 0),
    (PRIMELLCSSCSSetup, 80, 0),
    (PRIMEPhysicalCounters, 81, 0),
    (PRIMEMACSetup, 82, 0),
    (PRIMEMACFuncParams, 83, 0),
    (PRIMEMACCounters, 84, 0),
    (PRIMEMACNetworkAdmin, 85, 0),
    (PRIMEAppIdentification, 86, 0),
    (G3MACCounters, 90, 1),
    (G3MACSetup, 91, 4),
    (G36LoWPANSetup, 92, 4),
    (G3HybridRFCounters, 160, 0),
    (G3HybridRFSetup, 161, 1),
    (G3Hybrid6LoWPANSetup, 162, 1),
    (HSPLCMACSetup, 140, 0),
    (HSPLCCPASSetup, 141, 0),
    (HSPLCIPSSASSetup, 142, 0),
    (HSPLCHDLCSSASSetup, 143, 0),
    (ZigbeeSASStartup, 101, 0),
    (ZigbeeSASJoin, 102, 0),
    (ZigbeeSASAPSFragmentation, 103, 0),
    (ZigbeeNetworkControl, 104, 0),
    (ZigbeeTunnelSetup, 105, 0),
    (SCHCLPWANSetup, 126, 0),
    (SCHCLPWANDiagnostic, 127, 0),
    (LoRaWANSetup, 128, 0),
    (LoRaWANDiagnostic, 129, 0),
    (WiSUNSetup, 95, 0),
    (WiSUNDiagnostic, 96, 0),
    (RPLDiagnostic, 97, 0),
    (MPLDiagnostic, 98, 0),
    (IEC14908Identification, 130, 0),
    (IEC14908ProtocolSetup, 131, 0),
    (IEC14908ProtocolStatus, 132, 0),
    (IEC14908Diagnostic, 133, 0),
    (TokenGateway, 115, 0),
    (IEC62055Attributes, 116, 0),
]


@pytest.mark.parametrize("cls,expected_id,expected_version", CLASS_SPECS)
def test_class_id_and_version(cls, expected_id, expected_version):
    """Verify CLASS_ID and VERSION match Blue Book Ed.16."""
    assert cls.CLASS_ID == expected_id, f"{cls.__name__}: CLASS_ID {cls.CLASS_ID} != {expected_id}"
    assert cls.VERSION == expected_version, f"{cls.__name__}: VERSION {cls.VERSION} != {expected_version}"


@pytest.mark.parametrize("cls,expected_id,expected_version", CLASS_SPECS)
def test_instantiation(cls, expected_id, expected_version):
    """Verify each IC class can be instantiated with default values."""
    obj = cls(logical_name=LN)
    assert obj.logical_name == LN
    assert obj.CLASS_ID == expected_id


def test_total_class_count():
    """Verify we have all 57 new classes covered."""
    assert len(CLASS_SPECS) == 57
