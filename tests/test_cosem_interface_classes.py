"""Tests for COSEM Blue Book interface classes."""
import pytest

from dlms_cosem import enumerations as enums
from dlms_cosem.cosem.obis import Obis
from dlms_cosem.cosem.data import Data
from dlms_cosem.cosem.register import Register
from dlms_cosem.cosem.register_monitor import RegisterMonitor
from dlms_cosem.cosem.register_activation import RegisterActivation
from dlms_cosem.cosem.demand_register import DemandRegister
from dlms_cosem.cosem.register_table import RegisterTable
from dlms_cosem.cosem.single_action_schedule import SingleActionSchedule
from dlms_cosem.cosem.action_schedule import ActionSchedule
from dlms_cosem.cosem.script_table import ScriptTable
from dlms_cosem.cosem.clock import Clock
from dlms_cosem.cosem.special_day_table import SpecialDayTable, SpecialDayEntry
from dlms_cosem.cosem.tariff_plan import TariffPlan
from dlms_cosem.cosem.tariff_table import TariffTable
from dlms_cosem.cosem.season_profile import SeasonProfile, SeasonProfileEntry
from dlms_cosem.cosem.week_profile import WeekProfile, WeekProfileEntry
from dlms_cosem.cosem.day_profile import DayProfile, DayProfileEntry
from dlms_cosem.cosem.lp_setup import LocalPortSetup
from dlms_cosem.cosem.rs485_setup import RS485Setup
from dlms_cosem.cosem.infrared_setup import InfraredSetup
from dlms_cosem.cosem.modem_setup import ModemSetup
from dlms_cosem.cosem.auto_answer import AutoAnswer
from dlms_cosem.cosem.modem_configuration import ModemConfiguration
from dlms_cosem.cosem.nbp_setup import NBIoTProfileSetup
from dlms_cosem.cosem.lora_setup import LoRaWANSetup, LoRaWANClass, LoRaBand
from dlms_cosem.cosem.event_log import EventLog, EventLogEntry
from dlms_cosem.cosem.security_setup import SecuritySetup, SecurityPolicy, CipherAlgorithm
from dlms_cosem.cosem.association_sn import AssociationSN
from dlms_cosem.cosem.energy_register import (
    create_energy_register, OBIS_ACTIVE_IMPORT, OBIS_ACTIVE_EXPORT,
)
from dlms_cosem.cosem.power_register import create_power_register
from dlms_cosem.cosem.voltage import create_voltage_register
from dlms_cosem.cosem.current import create_current_register
from dlms_cosem.cosem.power_factor import create_pf_register
from dlms_cosem.cosem.frequency import create_frequency_register


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
