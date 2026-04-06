"""Tests for COSEM Blue Book interface classes."""
import pytest

from dlms_cosem import enumerations as enums
from dlms_cosem.cosem.obis import Obis
from dlms_cosem.cosem.C1_Data import Data
from dlms_cosem.cosem.C2_Register import Register
from dlms_cosem.cosem.C13_RegisterMonitor import RegisterMonitor
from dlms_cosem.cosem.C14_RegisterActivation import RegisterActivation
from dlms_cosem.cosem.C4_DemandRegister import DemandRegister
from dlms_cosem.cosem.C61_RegisterTable import RegisterTable
from dlms_cosem.cosem.single_action_schedule import SingleActionSchedule
from dlms_cosem.cosem.C9_ActionSchedule import ActionSchedule
from dlms_cosem.cosem.C7_ScriptTable import ScriptTable
from dlms_cosem.cosem.C6_Clock import Clock
from dlms_cosem.cosem.C8_SpecialDayTable import SpecialDayTable, SpecialDayEntry
from dlms_cosem.cosem.tariff_plan import TariffPlan
from dlms_cosem.cosem.tariff_table import TariffTable
from dlms_cosem.cosem.season_profile import SeasonProfile, SeasonProfileEntry
from dlms_cosem.cosem.week_profile import WeekProfile, WeekProfileEntry
from dlms_cosem.cosem.day_profile import DayProfile, DayProfileEntry
from dlms_cosem.cosem.C102_LocalPortSetup import LocalPortSetup
from dlms_cosem.cosem.C23_RS485Setup import RS485Setup
from dlms_cosem.cosem.C101_InfraredSetup import InfraredSetup
from dlms_cosem.cosem.C24_ModemSetup import ModemSetup
from dlms_cosem.cosem.C28_AutoAnswer import AutoAnswer
from dlms_cosem.cosem.C48_ModemConfiguration import ModemConfiguration
from dlms_cosem.cosem.C106_NBIoTProfileSetup import NBIoTProfileSetup
from dlms_cosem.cosem.C107_LoRaWANSetup import LoRaWANSetup, LoRaWANClass, LoRaBand
from dlms_cosem.cosem.C76_EventLog import EventLog, EventLogEntry
from dlms_cosem.cosem.C29_SecuritySetup import SecuritySetup, SecurityPolicy, CipherAlgorithm
from dlms_cosem.cosem.C10_AssociationSN import AssociationSN
from dlms_cosem.cosem.energy_register import (
    create_energy_register, OBIS_ACTIVE_IMPORT, OBIS_ACTIVE_EXPORT,
)
from dlms_cosem.cosem.power_register import create_power_register
from dlms_cosem.cosem.voltage import create_voltage_register
from dlms_cosem.cosem.current import create_current_register
from dlms_cosem.cosem.power_factor import create_pf_register
from dlms_cosem.cosem.frequency import create_frequency_register
from dlms_cosem.cosem.C119_ValueTable import ValueTable, ValueEntry, ValueDescriptor
from dlms_cosem.cosem.C32_IecPublicKey import IecPublicKey, KeyAlgorithm, KeyUsage
from dlms_cosem.cosem.C83_MbusDiagnostic import MbusDiagnostic
from dlms_cosem.cosem.C110_PowerQualityMonitor import PowerQualityMonitor
from dlms_cosem.cosem.C111_HarmonicMonitor import HarmonicMonitor, MonitoringMode
from dlms_cosem.cosem.C112_SagSwellMonitor import SagSwellMonitor
from dlms_cosem.cosem.C62_CompactData import CompactData, CompactDataField
from dlms_cosem.cosem.C55_StatusMapping import StatusMapping, StatusMappingEntry
from dlms_cosem.cosem.C33_CosemDataProtection import CosemDataProtection, ProtectedObject
from dlms_cosem.cosem.C78_FunctionControl import FunctionControl, FunctionControlEntry
from dlms_cosem.cosem.C211_ArrayManager import ArrayManager
from dlms_cosem.cosem.C115_CommPortProtection import CommPortProtection, ProtectedPort
from dlms_cosem.cosem.C18_ActivityCalendar import ActivityCalendar, ActivityPeriod
from dlms_cosem.cosem.C53_SapAssignment import SapAssignment, SapAssignmentEntry

OBIS = Obis.from_string("0.0.1.0.0.255")


class TestData:
    def test_create(self):
        d = Data(logical_name=OBIS, value=42)
        assert d.value == 42
        assert d.CLASS_ID == enums.CosemInterface.DATA

    def test_reset(self):
        d = Data(logical_name=OBIS, value=42)
        d.reset()
        assert d.value is None

    def test_is_static(self):
        d = Data(logical_name=OBIS)
        assert d.is_static_attribute(1)
        assert not d.is_static_attribute(2)


class TestRegister:
    def test_create(self):
        r = Register(logical_name=OBIS, value=12345, scaler=-3, unit=1)
        assert r.value == 12345
        assert r.CLASS_ID == enums.CosemInterface.REGISTER

    def test_reset(self):
        r = Register(logical_name=OBIS, value=100)
        r.reset()
        assert r.value == 0


class TestDemandRegister:
    def test_create(self):
        dr = DemandRegister(logical_name=OBIS, current_value=500, period=900)
        assert dr.current_value == 500
        assert dr.period == 900

    def test_next_period(self):
        dr = DemandRegister(logical_name=OBIS, current_value=500, last_average_value=400)
        dr.next_period()
        assert dr.last_average_value == 500
        assert dr.current_value == 0

    def test_reset(self):
        dr = DemandRegister(logical_name=OBIS, current_value=100, last_average_value=90)
        dr.reset()
        assert dr.current_value == 0
        assert dr.last_average_value == 0


class TestClock:
    def test_create(self):
        c = Clock(logical_name=OBIS, time_zone=480)
        assert c.time_zone == 480
        assert c.CLASS_ID == enums.CosemInterface.CLOCK

    def test_adjust_time(self):
        from datetime import datetime, timedelta
        c = Clock(logical_name=OBIS, time=datetime(2024, 1, 1, 12, 0, 0))
        c.adjust_time(60)
        assert c.time == datetime(2024, 1, 1, 13, 0, 0)


class TestSpecialDayTable:
    def test_add_remove(self):
        sdt = SpecialDayTable(logical_name=OBIS)
        entry = SpecialDayEntry(day_index=1, day_profile_id=3)
        sdt.add_entry(entry)
        assert len(sdt.special_day_table) == 1
        sdt.remove_entry(1)
        assert len(sdt.special_day_table) == 0


class TestEventLog:
    def test_add_event(self):
        el = EventLog(logical_name=OBIS)
        el.add_event(1)
        assert len(el.entries) == 1

    def test_reset(self):
        el = EventLog(logical_name=OBIS)
        el.add_event(1)
        el.reset()
        assert len(el.entries) == 0


class TestRegisterActivation:
    def test_activate_deactivate(self):
        ra = RegisterActivation(logical_name=OBIS, active_mask=0)
        ra.activate(0x01)
        assert ra.active_mask == 0x01
        ra.deactivate(0x01)
        assert ra.active_mask == 0x00


class TestRegisterTable:
    def test_reset(self):
        rt = RegisterTable(logical_name=OBIS, values=[[1, 2], [3, 4]])
        rt.reset()
        assert rt.values == []


class TestActionSchedule:
    def test_add_remove(self):
        asched = ActionSchedule(logical_name=OBIS)
        asched.add_entry("test_entry")
        assert len(asched.action_schedule) == 1
        asched.remove_entry(0)
        assert len(asched.action_schedule) == 0


class TestScriptTable:
    def test_create(self):
        st = ScriptTable(logical_name=OBIS, scripts=[["action1"], ["action2"]])
        assert len(st.scripts) == 2


class TestCommunicationSetup:
    def test_local_port_setup(self):
        lp = LocalPortSetup(logical_name=OBIS, default_baudrate=300)
        assert lp.default_baudrate == 300
        lp.change_baudrate(9600)
        assert lp.proposed_baudrate == 9600

    def test_rs485_setup(self):
        rs = RS485Setup(logical_name=OBIS, address=1)
        assert rs.address == 1

    def test_infrared_setup(self):
        ir = InfraredSetup(logical_name=OBIS)
        assert ir.baudrate == 9600

    def test_modem_setup(self):
        ms = ModemSetup(logical_name=OBIS, phone_number="12345678")
        assert ms.phone_number == "12345678"

    def test_auto_answer(self):
        aa = AutoAnswer(logical_name=OBIS, number_of_rings=5)
        assert aa.number_of_rings == 5


class TestNBIoTSetup:
    def test_create(self):
        nb = NBIoTProfileSetup(
            logical_name=OBIS,
            plmn="46000",
            apn="nbiot",
            psm_enabled=True,
            dtls_enabled=True,
        )
        assert nb.plmn == "46000"
        assert nb.psm_enabled is True
        assert nb.CLASS_ID == 106


class TestLoRaWANSetup:
    def test_create(self):
        ls = LoRaWANSetup(
            logical_name=OBIS,
            dev_eui=b"\x01\x02\x03\x04\x05\x06\x07\x08",
            lora_class=LoRaWANClass.CLASS_A,
            band=LoRaBand.CN470,
        )
        assert ls.band == LoRaBand.CN470
        assert ls.CLASS_ID == 107

    def test_join_reset(self):
        ls = LoRaWANSetup(logical_name=OBIS)
        ls.join()
        ls.reset()
        assert ls.dev_addr is None


class TestSecuritySetup:
    def test_create(self):
        ss = SecuritySetup(
            logical_name=OBIS,
            security_policy=SecurityPolicy.AUTHENTICATED_ENCRYPTED,
            security_suite=0,
            cipher_algorithm=CipherAlgorithm.AES_128_GCM,
        )
        assert ss.security_policy == SecurityPolicy.AUTHENTICATED_ENCRYPTED

    def test_methods_exist(self):
        ss = SecuritySetup(logical_name=OBIS)
        assert hasattr(ss, 'add_key')
        assert hasattr(ss, 'change_key')


class TestAssociationSN:
    def test_create(self):
        asn = AssociationSN(
            logical_name=OBIS,
            hls_auth_mechanism=enums.AuthenticationMechanism.HLS_GMAC,
        )
        assert asn.CLASS_ID == enums.CosemInterface.ASSOCIATION_SN


class TestEnergyRegister:
    def test_create_active_import(self):
        er = create_energy_register(OBIS_ACTIVE_IMPORT, value=100000, scaler=-3)
        assert er.value == 100000
        assert er.logical_name.to_string() == "1-0:1.8.0.255"

    def test_create_active_export(self):
        er = create_energy_register(OBIS_ACTIVE_EXPORT, value=50000)
        assert er.logical_name.to_string() == "1-0:2.8.0.255"


class TestPowerRegister:
    def test_create(self):
        pr = create_power_register("1.0.11.7.0.255", value=2500)
        assert pr.value == 2500


class TestVoltageRegister:
    def test_create(self):
        vr = create_voltage_register()
        assert vr.value == 220.0


class TestCurrentRegister:
    def test_create(self):
        cr = create_current_register()
        assert cr.value == 5.0


class TestFrequencyRegister:
    def test_create(self):
        fr = create_frequency_register()
        assert fr.value == 50.0


class TestTariffProfiles:
    def test_season_profile(self):
        sp = SeasonProfile(logical_name=OBIS)
        sp.season_profile.append(SeasonProfileEntry(season_name="summer", week_profile_name="wp1"))
        assert len(sp.season_profile) == 1

    def test_week_profile(self):
        wp = WeekProfile(logical_name=OBIS)
        wp.week_profile.append(WeekProfileEntry(week_name="normal"))
        assert len(wp.week_profile) == 1

    def test_day_profile(self):
        dp = DayProfile(logical_name=OBIS)
        dp.day_profile.append(DayProfileEntry(start_time="08:00", tariff_index=2))
        assert len(dp.day_profile) == 1


class TestValueTable:
    def test_create(self):
        vt = ValueTable(logical_name=OBIS)
        assert vt.CLASS_ID == enums.CosemInterface.VALUE_TABLE
        assert len(vt.values) == 0
        assert len(vt.descriptors) == 0

    def test_add_value(self):
        vt = ValueTable(logical_name=OBIS)
        entry = ValueEntry(index=1, value=100)
        vt.add_value(entry)
        assert len(vt.values) == 1
        assert vt.values[0].index == 1

    def test_add_descriptor(self):
        vt = ValueTable(logical_name=OBIS)
        desc = ValueDescriptor(index=1, description="Voltage", unit=27, scaler=0)
        vt.add_descriptor(desc)
        assert len(vt.descriptors) == 1
        assert vt.descriptors[0].description == "Voltage"

    def test_remove_value(self):
        vt = ValueTable(logical_name=OBIS)
        entry = ValueEntry(index=1, value=100)
        vt.add_value(entry)
        removed = vt.remove_value(0)
        assert removed is not None
        assert removed.index == 1
        assert len(vt.values) == 0

    def test_get_value_by_index(self):
        vt = ValueTable(logical_name=OBIS)
        entry1 = ValueEntry(index=1, value=100)
        entry2 = ValueEntry(index=2, value=200)
        vt.add_value(entry1)
        vt.add_value(entry2)
        found = vt.get_value_by_index(2)
        assert found is not None
        assert found.value == 200

    def test_get_descriptor_by_index(self):
        vt = ValueTable(logical_name=OBIS)
        desc1 = ValueDescriptor(index=1, description="Voltage", unit=27, scaler=0)
        desc2 = ValueDescriptor(index=2, description="Current", unit=34, scaler=0)
        vt.add_descriptor(desc1)
        vt.add_descriptor(desc2)
        found = vt.get_descriptor_by_index(2)
        assert found is not None
        assert found.description == "Current"

    def test_is_static_attribute(self):
        vt = ValueTable(logical_name=OBIS)
        assert vt.is_static_attribute(1)
        assert not vt.is_static_attribute(2)


class TestIecPublicKey:
    def test_create(self):
        key = IecPublicKey(logical_name=OBIS)
        assert key.CLASS_ID == enums.CosemInterface.IEC_PUBLIC_KEY
        assert key.public_key == b""
        assert key.key_id == ""

    def test_with_key_data(self):
        key = IecPublicKey(logical_name=OBIS)
        key.public_key = b"\x01\x02\x03\x04"
        key.key_id = "key-001"
        assert len(key.public_key) == 4
        assert key.key_id == "key-001"

    def test_validate(self):
        key = IecPublicKey(logical_name=OBIS)
        assert not key.validate()
        key.public_key = b"test-key"
        key.key_id = "key-id"
        assert key.validate()

    def test_is_valid(self):
        key = IecPublicKey(logical_name=OBIS)
        key.public_key = b"valid-key"
        key.key_id = "valid-id"
        assert key.is_valid()

    def test_algorithm_names(self):
        key = IecPublicKey(logical_name=OBIS)
        key.algorithm = KeyAlgorithm.RSA
        assert key.get_algorithm_name() == "RSA"
        key.algorithm = KeyAlgorithm.ECC
        assert key.get_algorithm_name() == "ECC"

    def test_key_usage_names(self):
        key = IecPublicKey(logical_name=OBIS)
        key.key_usage = KeyUsage.ENCRYPTION
        assert key.get_key_usage_name() == "Encryption"
        key.key_usage = KeyUsage.SIGNATURE
        assert key.get_key_usage_name() == "Signature"

    def test_is_static_attribute(self):
        key = IecPublicKey(logical_name=OBIS)
        assert key.is_static_attribute(1)
        assert not key.is_static_attribute(2)


class TestMbusDiagnostic:
    def test_create(self):
        diag = MbusDiagnostic(logical_name=OBIS)
        assert diag.CLASS_ID == enums.CosemInterface.MBUS_DIAGNOSTIC
        assert diag.total_messages_sent == 0
        assert diag.total_messages_received == 0

    def test_increment_counters(self):
        diag = MbusDiagnostic(logical_name=OBIS)
        diag.increment_sent()
        diag.increment_received()
        assert diag.total_messages_sent == 1
        assert diag.total_messages_received == 1

    def test_error_counters(self):
        diag = MbusDiagnostic(logical_name=OBIS)
        diag.increment_failed()
        diag.increment_crc_error()
        diag.increment_timeout_error()
        assert diag.failed_messages == 1
        assert diag.crc_errors == 1
        assert diag.timeout_errors == 1

    def test_set_signal_quality(self):
        diag = MbusDiagnostic(logical_name=OBIS)
        diag.set_signal_quality(85)
        assert diag.signal_quality == 85
        diag.set_signal_quality(150)  # Should be clamped
        assert diag.signal_quality == 100

    def test_set_bus_voltage(self):
        diag = MbusDiagnostic(logical_name=OBIS)
        diag.set_bus_voltage(24.5)
        assert diag.bus_voltage == 24.5

    def test_success_rate(self):
        diag = MbusDiagnostic(logical_name=OBIS)
        diag.total_messages_sent = 95
        diag.total_messages_received = 100
        diag.failed_messages = 5
        rate = diag.get_success_rate()
        assert abs(rate - 97.37) < 0.1

    def test_total_errors(self):
        diag = MbusDiagnostic(logical_name=OBIS)
        diag.failed_messages = 3
        diag.crc_errors = 2
        diag.timeout_errors = 1
        assert diag.get_total_errors() == 6

    def test_reset_counters(self):
        diag = MbusDiagnostic(logical_name=OBIS)
        diag.total_messages_sent = 10
        diag.failed_messages = 2
        diag.reset_counters()
        assert diag.total_messages_sent == 0
        assert diag.failed_messages == 0

    def test_is_static_attribute(self):
        diag = MbusDiagnostic(logical_name=OBIS)
        assert diag.is_static_attribute(1)
        assert not diag.is_static_attribute(2)


class TestPowerQualityMonitor:
    def test_create(self):
        pqm = PowerQualityMonitor(logical_name=OBIS)
        assert pqm.CLASS_ID == enums.CosemInterface.POWER_QUALITY_MONITOR
        assert pqm.voltage_sag_count == 0
        assert pqm.power_factor_avg == 100

    def test_increment_events(self):
        pqm = PowerQualityMonitor(logical_name=OBIS)
        pqm.increment_sag()
        pqm.increment_sag()
        pqm.increment_swell()
        pqm.increment_interruption()
        assert pqm.voltage_sag_count == 2
        assert pqm.voltage_swell_count == 1
        assert pqm.interruption_count == 1

    def test_voltage_unbalance(self):
        pqm = PowerQualityMonitor(logical_name=OBIS)
        pqm.set_voltage_unbalance(5)
        assert pqm.voltage_unbalance == 5
        pqm.set_voltage_unbalance(150)  # Should be clamped
        assert pqm.voltage_unbalance == 100

    def test_frequency_deviation(self):
        pqm = PowerQualityMonitor(logical_name=OBIS)
        pqm.set_frequency_deviation(-5)  # -0.05 Hz
        assert pqm.frequency_deviation == -5

    def test_thd(self):
        pqm = PowerQualityMonitor(logical_name=OBIS)
        pqm.set_thd_voltage(5)
        pqm.set_thd_current(8)
        assert pqm.thd_voltage == 5
        assert pqm.thd_current == 8

    def test_power_factor(self):
        pqm = PowerQualityMonitor(logical_name=OBIS)
        pqm.set_power_factor_avg(95)
        assert pqm.power_factor_avg == 95
        assert abs(pqm.get_power_factor_decimal() - 0.95) < 0.01

    def test_total_events(self):
        pqm = PowerQualityMonitor(logical_name=OBIS)
        pqm.increment_sag()
        pqm.increment_swell()
        pqm.increment_interruption()
        assert pqm.get_total_events() == 3

    def test_reset_counters(self):
        pqm = PowerQualityMonitor(logical_name=OBIS)
        pqm.increment_sag()
        pqm.increment_swell()
        pqm.reset_counters()
        assert pqm.voltage_sag_count == 0
        assert pqm.voltage_swell_count == 0

    def test_is_static_attribute(self):
        pqm = PowerQualityMonitor(logical_name=OBIS)
        assert pqm.is_static_attribute(1)
        assert not pqm.is_static_attribute(2)


class TestHarmonicMonitor:
    def test_create(self):
        hm = HarmonicMonitor(logical_name=OBIS)
        assert hm.CLASS_ID == enums.CosemInterface.HARMONIC_MONITOR
        assert len(hm.voltage_harmonics) == 63
        assert len(hm.current_harmonics) == 63

    def test_voltage_harmonics(self):
        hm = HarmonicMonitor(logical_name=OBIS)
        hm.set_voltage_harmonic(1, 100)
        hm.set_voltage_harmonic(3, 5)
        hm.set_voltage_harmonic(5, 3)
        assert hm.get_voltage_harmonic(1) == 100
        assert hm.get_voltage_harmonic(3) == 5
        assert hm.get_voltage_harmonic(5) == 3

    def test_current_harmonics(self):
        hm = HarmonicMonitor(logical_name=OBIS)
        hm.set_current_harmonic(1, 80)
        hm.set_current_harmonic(7, 10)
        assert hm.get_current_harmonic(1) == 80
        assert hm.get_current_harmonic(7) == 10

    def test_invalid_harmonic_order(self):
        hm = HarmonicMonitor(logical_name=OBIS)
        assert hm.get_voltage_harmonic(100) == 0
        assert not hm.set_voltage_harmonic(100, 5)

    def test_thd_calculation_voltage(self):
        hm = HarmonicMonitor(logical_name=OBIS)
        hm.voltage_harmonics[0] = 100  # Fundamental
        hm.voltage_harmonics[2] = 5   # 3rd harmonic
        hm.voltage_harmonics[4] = 3   # 5th harmonic
        thd = hm.calculate_thd_voltage()
        assert thd > 0
        assert thd <= 100

    def test_thd_calculation_current(self):
        hm = HarmonicMonitor(logical_name=OBIS)
        hm.current_harmonics[0] = 80  # Fundamental
        hm.current_harmonics[2] = 10  # 3rd harmonic
        thd = hm.calculate_thd_current()
        assert thd > 0
        assert thd <= 100

    def test_monitoring_mode(self):
        hm = HarmonicMonitor(logical_name=OBIS)
        hm.set_monitoring_mode(MonitoringMode.VOLTAGE_ONLY)
        assert hm.get_monitoring_mode_name() == "Voltage Only"
        hm.set_monitoring_mode(MonitoringMode.BOTH)
        assert hm.get_monitoring_mode_name() == "Both"

    def test_sample_rate(self):
        hm = HarmonicMonitor(logical_name=OBIS)
        hm.set_sample_rate(512)
        assert hm.sample_rate == 512

    def test_reset_harmonics(self):
        hm = HarmonicMonitor(logical_name=OBIS)
        hm.set_voltage_harmonic(1, 100)
        hm.set_current_harmonic(1, 80)
        hm.reset_harmonics()
        assert hm.get_voltage_harmonic(1) == 0
        assert hm.get_current_harmonic(1) == 0

    def test_is_static_attribute(self):
        hm = HarmonicMonitor(logical_name=OBIS)
        assert hm.is_static_attribute(1)
        assert not hm.is_static_attribute(2)


class TestSagSwellMonitor:
    def test_create(self):
        ssm = SagSwellMonitor(logical_name=OBIS)
        assert ssm.CLASS_ID == enums.CosemInterface.SAG_SWELL_MONITOR
        assert ssm.sag_threshold_percent == 90
        assert ssm.swell_threshold_percent == 110

    def test_thresholds(self):
        ssm = SagSwellMonitor(logical_name=OBIS)
        ssm.set_sag_threshold_percent(85)
        ssm.set_swell_threshold_percent(115)
        assert ssm.sag_threshold_percent == 85
        assert ssm.swell_threshold_percent == 115

    def test_record_sag(self):
        ssm = SagSwellMonitor(logical_name=OBIS)
        ssm.record_sag(80, 5000)
        assert ssm.sag_count == 1
        assert ssm.last_sag_depth_percent == 80
        assert ssm.sag_duration_ms == 5000

    def test_record_swell(self):
        ssm = SagSwellMonitor(logical_name=OBIS)
        ssm.record_swell(125, 3000)
        assert ssm.swell_count == 1
        assert ssm.last_swell_magnitude_percent == 125
        assert ssm.swell_duration_ms == 3000

    def test_check_voltage(self):
        ssm = SagSwellMonitor(logical_name=OBIS)
        assert ssm.check_voltage(95) == "normal"
        assert ssm.check_voltage(80) == "sag"
        assert ssm.check_voltage(120) == "swell"

    def test_monitoring_enabled(self):
        ssm = SagSwellMonitor(logical_name=OBIS)
        assert ssm.is_monitoring_enabled()
        ssm.set_monitoring_enabled(False)
        assert not ssm.is_monitoring_enabled()
        assert ssm.check_voltage(50) == "normal"  # Disabled

    def test_total_events(self):
        ssm = SagSwellMonitor(logical_name=OBIS)
        ssm.record_sag(80, 1000)
        ssm.record_sag(85, 2000)
        ssm.record_swell(120, 3000)
        assert ssm.get_total_events() == 3

    def test_reset_counters(self):
        ssm = SagSwellMonitor(logical_name=OBIS)
        ssm.record_sag(80, 1000)
        ssm.record_swell(120, 3000)
        ssm.reset_counters()
        assert ssm.sag_count == 0
        assert ssm.swell_count == 0
        assert ssm.sag_duration_ms == 0
        assert ssm.swell_duration_ms == 0

    def test_is_static_attribute(self):
        ssm = SagSwellMonitor(logical_name=OBIS)
        assert ssm.is_static_attribute(1)
        assert not ssm.is_static_attribute(2)


class TestCompactData:
    def test_create(self):
        cd = CompactData(logical_name=OBIS)
        assert cd.CLASS_ID == enums.CosemInterface.COMPACT_DATA
        assert cd.buffer == b""

    def test_set_buffer(self):
        cd = CompactData(logical_name=OBIS)
        cd.set_buffer(b"\x01\x02\x03")
        assert cd.buffer == b"\x01\x02\x03"

    def test_bitmap_operations(self):
        cd = CompactData(logical_name=OBIS)
        cd.set_bitmap(0xFF)
        assert cd.bitmap == 0xFF

    def test_add_field(self):
        cd = CompactData(logical_name=OBIS)
        from dlms_cosem.cosem.C62_CompactData import CompactDataField
        field = CompactDataField(index=1, value=100, offset=0, length=4)
        cd.add_field(field)
        assert len(cd.fields) == 1


class TestStatusMapping:
    def test_create(self):
        sm = StatusMapping(logical_name=OBIS)
        assert sm.CLASS_ID == enums.CosemInterface.STATUS_MAPPING
        assert sm.default_external_status == 0

    def test_add_mapping(self):
        sm = StatusMapping(logical_name=OBIS)
        sm.add_mapping(1, 10, "Status 1")
        assert len(sm.mappings) == 1

    def test_map_status(self):
        sm = StatusMapping(logical_name=OBIS)
        sm.add_mapping(1, 10, "Status 1")
        assert sm.map_status(1) == 10

    def test_remove_mapping(self):
        sm = StatusMapping(logical_name=OBIS)
        sm.add_mapping(1, 10, "Status 1")
        sm.remove_mapping(1)
        assert len(sm.mappings) == 0


class TestCosemDataProtection:
    def test_create(self):
        cdp = CosemDataProtection(logical_name=OBIS)
        assert cdp.CLASS_ID == enums.CosemInterface.COSEM_DATA_PROTECTION
        assert cdp.protection_enabled is True

    def test_add_protection(self):
        cdp = CosemDataProtection(logical_name=OBIS)
        cdp.add_protection(1, b"\x00\x00\x01\x00\x00\xff", 1, 2)
        assert len(cdp.protected_objects) == 1

    def test_check_access(self):
        cdp = CosemDataProtection(logical_name=OBIS)
        cdp.add_protection(1, b"\x00\x00\x01\x00\x00\xff", 1, 2)
        assert cdp.check_access(1, b"\x00\x00\x01\x00\x00\xff", "read", 1)

    def test_disable_protection(self):
        cdp = CosemDataProtection(logical_name=OBIS)
        cdp.set_protection_enabled(False)
        assert not cdp.protection_enabled


class TestFunctionControl:
    def test_create(self):
        fc = FunctionControl(logical_name=OBIS)
        assert fc.CLASS_ID == enums.CosemInterface.FUNCTION_CONTROL
        assert fc.execution_policy == 0

    def test_add_function(self):
        fc = FunctionControl(logical_name=OBIS)
        fc.add_function("func1", b"\x00\x00\x01\x00\x00\xff", 1)
        assert len(fc.functions) == 1

    def test_enable_disable_function(self):
        fc = FunctionControl(logical_name=OBIS)
        fc.add_function("func1", b"\x00\x00\x01\x00\x00\xff", 1)
        fc.disable_function("func1")
        assert not fc.is_function_enabled("func1")
        fc.enable_function("func1")
        assert fc.is_function_enabled("func1")

    def test_execution_policy(self):
        fc = FunctionControl(logical_name=OBIS)
        fc.set_execution_policy(2)
        assert fc.execution_policy == 2


class TestArrayManager:
    def test_create(self):
        am = ArrayManager(logical_name=OBIS)
        assert am.CLASS_ID == enums.CosemInterface.ARRAY_MANAGER
        assert am.array_size == 0

    def test_append_element(self):
        am = ArrayManager(logical_name=OBIS)
        am.append_element(100)
        assert len(am.data_array) == 1
        assert am.array_size == 1

    def test_set_element(self):
        am = ArrayManager(logical_name=OBIS)
        am.append_element(100)
        am.set_element(0, 200)
        assert am.data_array[0] == 200

    def test_get_slice(self):
        am = ArrayManager(logical_name=OBIS)
        am.append_element(1)
        am.append_element(2)
        am.append_element(3)
        am.append_element(4)
        am.append_element(5)
        slice_data = am.get_slice(1, 4)
        assert slice_data == [2, 3, 4]


class TestCommPortProtection:
    def test_create(self):
        cpp = CommPortProtection(logical_name=OBIS)
        assert cpp.CLASS_ID == enums.CosemInterface.COMMUNICATION_PORT_PROTECTION
        assert cpp.protection_enabled is True

    def test_add_port_protection(self):
        cpp = CommPortProtection(logical_name=OBIS)
        cpp.add_port_protection(1, 2, 5)
        assert len(cpp.protected_ports) == 1

    def test_check_port_access(self):
        cpp = CommPortProtection(logical_name=OBIS)
        cpp.add_port_protection(1, 2, 5)
        assert not cpp.check_port_access(1, 1)  # Insufficient level
        assert cpp.check_port_access(1, 2)  # Sufficient level

    def test_disable_protection(self):
        cpp = CommPortProtection(logical_name=OBIS)
        cpp.set_protection_enabled(False)
        assert not cpp.protection_enabled


class TestActivityCalendar:
    def test_create(self):
        ac = ActivityCalendar(logical_name=OBIS)
        assert ac.CLASS_ID == enums.CosemInterface.ACTIVITY_CALENDAR
        assert ac.calendar_name == ""

    def test_add_period(self):
        ac = ActivityCalendar(logical_name=OBIS)
        ac.add_period("01-01", "12-31", 1, "Full Year")
        assert len(ac.activity_periods) == 1

    def test_get_activity_for_date(self):
        ac = ActivityCalendar(logical_name=OBIS)
        ac.add_period("01-01", "06-30", 1, "First Half")
        ac.add_period("07-01", "12-31", 2, "Second Half")
        assert ac.get_activity_for_date("03-15") == 1
        assert ac.get_activity_for_date("08-20") == 2

    def test_remove_period(self):
        ac = ActivityCalendar(logical_name=OBIS)
        ac.add_period("01-01", "12-31", 1, "Full Year")
        ac.remove_period(1)
        assert len(ac.activity_periods) == 0


class TestSapAssignment:
    def test_create(self):
        sa = SapAssignment(logical_name=OBIS)
        assert sa.CLASS_ID == enums.CosemInterface.SAP_ASSIGNMENT
        assert sa.default_sap == 1

    def test_add_assignment(self):
        sa = SapAssignment(logical_name=OBIS)
        sa.add_assignment(1, b"\x01\x02\x03", 100, 1)
        assert len(sa.assignments) == 1

    def test_get_sap_for_context(self):
        sa = SapAssignment(logical_name=OBIS)
        ctx = b"\x01\x02\x03"
        sa.add_assignment(10, ctx, 100, 1)
        assert sa.get_sap_for_context(ctx) == 10

    def test_enable_disable(self):
        sa = SapAssignment(logical_name=OBIS)
        sa.add_assignment(1, b"\x01\x02\x03", 100, 1)
        sa.disable_assignment(1)
        assert not sa.is_assignment_enabled(1)
        sa.enable_assignment(1)
        assert sa.is_assignment_enabled(1)
