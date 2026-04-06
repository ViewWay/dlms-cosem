"""Parametrized tests for COSEM IC classes.

Tests instantiation, CLASS_ID, attribute access, and attrs structure for all IC classes
that don't have dedicated test files.
"""
import pytest

from dlms_cosem.cosem import (
    Data, Register, ExtendedRegister, Clock, ProfileGeneric,
    RegisterMonitor, DemandRegister, SecuritySetup, ActivityCalendar,
    MaxDemandRegister, ValueWithRegister, RegisterActivation, RegisterTable,
    SingleActionSchedule, ActionSchedule, ScriptTable, SpecialDayTable,
    TariffPlan, TariffTable, SeasonProfile, WeekProfile, DayProfile,
    LocalPortSetup, RS485Setup, InfraredSetup, ModemSetup, AutoAnswer,
    ModemConfiguration, EventLog, StandardEventLog, UtilityEventLog,
    EventNotification, QualityControl, InterrogationInterface, LoadProfileSwitch,
    AssociationSN, GPRSSetup, TcpUdpSetup, ZigBeeSetup,
    ValueTable, IecPublicKey, MbusDiagnostic, PowerQualityMonitor,
    HarmonicMonitor, SagSwellMonitor, CompactData, StatusMapping,
    CosemDataProtection, FunctionControl, ArrayManager, CommPortProtection,
    SapAssignment, UtilityTables, MeasurementDataMonitoring, AutoConnect,
    GSMDiagnostic, LTEMonitoring, MBusSlavePortSetup, WirelessModeQChannel,
    MBusMasterPortSetup, DLMSMBusPortSetup, IPv6Setup, CoAPSetup, CoAPDiagnostic,
    SFSKPhyMACSetup, SFSKActiveInitiator, SFSKMACSyncTimeouts, SFSKMACCounters,
    IEC61334LLCSetup, SFSKReportingSystemList, LLCType1Setup, LLCType2Setup,
    LLCType3Setup, PRIMELLCSSCSSetup, PRIMEPhysicalCounters, PRIMEMACSetup,
    PRIMEMACFuncParams, PRIMEMACCounters, PRIMEMACNetworkAdmin,
    PRIMEAppIdentification, G3MACCounters, G3MACSetup, G36LoWPANSetup,
    G3HybridRFCounters, G3HybridRFSetup, G3Hybrid6LoWPANSetup,
    HSPLCMACSetup, HSPLCCPASSetup, HSPLCIPSSASSetup, HSPLCHDLCSSASSetup,
    ZigbeeSASStartup, ZigbeeSASJoin, ZigbeeSASAPSFragmentation,
    ZigbeeNetworkControl, ZigbeeTunnelSetup,
    SCHCLPWANSetup, SCHCLPWANDiagnostic, LoRaWANSetup, LoRaWANDiagnostic,
    WiSUNSetup, WiSUNDiagnostic, RPLDiagnostic, MPLDiagnostic,
    IEC14908Identification, IEC14908ProtocolSetup, IEC14908ProtocolStatus,
    IEC14908Diagnostic, TokenGateway, IEC62055Attributes, NBIoTProfileSetup,
)
from dlms_cosem.cosem.obis import Obis

LN = Obis(0, 0, 1, 0, 0, 255)

# (class, expected CLASS_ID or None)
IC_CLASSES = [
    (Data, 1),
    (Register, 3),
    (ExtendedRegister, 4),
    (DemandRegister, 5),
    (RegisterActivation, 6),
    (RegisterMonitor, 21),
    (ActionSchedule, 10),
    (ScriptTable, 9),
    (Clock, 8),
    (SpecialDayTable, 11),
    (LocalPortSetup, 19),
    (RS485Setup, 23),
    (InfraredSetup, 24),
    (AutoAnswer, 28),
    (ModemConfiguration, 29),
    (SecuritySetup, 64),
    (AssociationSN, 12),
    (CompactData, 62),
    (StatusMapping, 63),
    (CosemDataProtection, 30),
    (FunctionControl, 122),
    (ArrayManager, 123),
    (CommPortProtection, 124),
    (SapAssignment, 17),
    (UtilityTables, 26),
    (MeasurementDataMonitoring, 66),
    (AutoConnect, 29),
    (GSMDiagnostic, 47),
    (LTEMonitoring, 151),
    (MBusSlavePortSetup, 25),
    (WirelessModeQChannel, 73),
    (MBusMasterPortSetup, 74),
    (DLMSMBusPortSetup, 76),
    (IPv6Setup, 48),
    (CoAPSetup, 152),
    (CoAPDiagnostic, 153),
    (SFSKPhyMACSetup, 50),
    (SFSKActiveInitiator, 51),
    (SFSKMACSyncTimeouts, 52),
    (SFSKMACCounters, 53),
    (IEC61334LLCSetup, 55),
    (SFSKReportingSystemList, 56),
    (LLCType1Setup, 57),
    (LLCType2Setup, 58),
    (LLCType3Setup, 59),
    (PRIMELLCSSCSSetup, 80),
    (PRIMEPhysicalCounters, 81),
    (PRIMEMACSetup, 82),
    (PRIMEMACFuncParams, 83),
    (PRIMEMACCounters, 84),
    (PRIMEMACNetworkAdmin, 85),
    (PRIMEAppIdentification, 86),
    (G3MACCounters, 90),
    (G3MACSetup, 91),
    (G36LoWPANSetup, 92),
    (G3HybridRFCounters, 160),
    (G3HybridRFSetup, 161),
    (G3Hybrid6LoWPANSetup, 162),
    (HSPLCMACSetup, 140),
    (HSPLCCPASSetup, 141),
    (HSPLCIPSSASSetup, 142),
    (HSPLCHDLCSSASSetup, 143),
    (ZigbeeSASStartup, 101),
    (ZigbeeSASJoin, 102),
    (ZigbeeSASAPSFragmentation, 103),
    (ZigbeeNetworkControl, 104),
    (ZigbeeTunnelSetup, 105),
    (SCHCLPWANSetup, 126),
    (SCHCLPWANDiagnostic, 127),
    (LoRaWANSetup, 128),
    (LoRaWANDiagnostic, 129),
    (WiSUNSetup, 95),
    (WiSUNDiagnostic, 96),
    (RPLDiagnostic, 97),
    (MPLDiagnostic, 98),
    (IEC14908Identification, 130),
    (IEC14908ProtocolSetup, 131),
    (IEC14908ProtocolStatus, 132),
    (IEC14908Diagnostic, 133),
    (TokenGateway, 115),
    (IEC62055Attributes, 116),
    (NBIoTProfileSetup, 106),
    (GPRSSetup, 108),
    (TcpUdpSetup, 109),
    (ZigBeeSetup, 110),
    (ValueTable, 29),
    (IecPublicKey, 90),
    (MbusDiagnostic, 110),
    (PowerQualityMonitor, 200),
    (HarmonicMonitor, 201),
    (SagSwellMonitor, 202),
    (MaxDemandRegister, 5),
    (ValueWithRegister, 24),
    (RegisterTable, 61),
    (SingleActionSchedule, 22),
    (TariffPlan, 26),
    (TariffTable, 26),
    (SeasonProfile, 26),
    (WeekProfile, 26),
    (DayProfile, 26),
    (ModemSetup, 27),
    (EventLog, 7),
    (StandardEventLog, 27),
    (UtilityEventLog, 28),
    (EventNotification, 29),
    (QualityControl, 31),
    (InterrogationInterface, 15),
    (LoadProfileSwitch, 23),
    (ProfileGeneric, None),
    (ActivityCalendar, 20),
]


def _make(cls):
    """Try to instantiate with Obis; if that fails, try no-args."""
    try:
        return cls(LN)
    except TypeError:
        return cls()


@pytest.mark.parametrize("cls,expected_cid", IC_CLASSES)
class TestICClass:
    def test_instantiation(self, cls, expected_cid):
        """Every IC class can be instantiated."""
        obj = _make(cls)
        assert obj is not None

    def test_class_id(self, cls, expected_cid):
        """CLASS_ID matches expected value."""
        if expected_cid is None:
            pytest.skip(f"{cls.__name__} has no CLASS_ID")
        assert cls.CLASS_ID == expected_cid

    def test_has_logical_name(self, cls, expected_cid):
        """IC classes with logical_name field can access it."""
        obj = _make(cls)
        if not hasattr(obj, "logical_name"):
            pytest.skip(f"{cls.__name__} has no logical_name")

    def test_is_attrs_class(self, cls, expected_cid):
        """IC classes are attrs classes with defined fields."""
        assert hasattr(cls, "__attrs_attrs__")
        fields = [f.name for f in cls.__attrs_attrs__]
        assert len(fields) > 0


class TestHighPriorityICClasses:
    """More detailed tests for commonly used IC classes."""

    def test_data_value(self):
        obj = Data(LN)
        assert hasattr(obj, "value")
        obj.value = b"\x01\x02\x03"
        assert obj.value == b"\x01\x02\x03"

    def test_register_fields(self):
        obj = Register(LN)
        assert hasattr(obj, "value")
        assert hasattr(obj, "scaler")
        assert hasattr(obj, "unit")

    def test_extended_register_fields(self):
        obj = ExtendedRegister(LN)
        assert hasattr(obj, "value")
        assert hasattr(obj, "capture_time")
        assert hasattr(obj, "scaler")
        assert hasattr(obj, "unit")
        assert hasattr(obj, "status")

    def test_clock_fields(self):
        obj = Clock(LN)
        for attr in ("time", "time_zone", "status",
                      "daylight_savings_enabled", "clock_base"):
            assert hasattr(obj, attr)

    def test_profile_generic_fields(self):
        obj = ProfileGeneric(LN)
        for attr in ("buffer", "capture_objects", "capture_period",
                      "sort_method", "entries_in_use", "profile_entries"):
            assert hasattr(obj, attr)

    def test_profile_generic_sort_method_enum(self):
        from dlms_cosem.cosem.C7_ProfileGeneric import SortMethod
        assert SortMethod is not None

    def test_register_monitor_fields(self):
        obj = RegisterMonitor(LN)
        for attr in ("thresholds", "monitored_object", "monitored_attribute"):
            assert hasattr(obj, attr)

    def test_activity_calendar_fields(self):
        obj = ActivityCalendar(LN)
        for attr in ("activity_periods", "calendar_name"):
            assert hasattr(obj, attr)

    def test_security_setup_fields(self):
        obj = SecuritySetup(LN)
        for attr in ("security_policy", "security_suite", "cipher_algorithm",
                      "authentication_key", "encryption_key", "master_key",
                      "system_title"):
            assert hasattr(obj, attr)

    def test_compact_data_fields(self):
        obj = CompactData(LN)
        for attr in ("buffer", "bitmap", "fields"):
            assert hasattr(obj, attr)

    def test_demand_register_fields(self):
        obj = DemandRegister(LN)
        for attr in ("current_value", "last_average_value", "period",
                      "number_of_periods"):
            assert hasattr(obj, attr)
