"""Tests for meter simulation example."""
import pytest
from dlms_cosem.cosem.obis import Obis
from examples.meter_simulation import MeterSimulation


class TestMeterSimulation:
    """Test complete meter simulation and data flow."""

    def setup_method(self):
        self.meter = MeterSimulation()

    def test_initialization(self):
        assert len(self.meter.objects) > 20
        assert not self.meter.connected

    def test_sn_association(self):
        assoc = self.meter.setup_sn_association(b"\x01\x02\x03\x04\x05\x06\x07\x08")
        assert self.meter.connected
        assert assoc is not None
        assert assoc.server_system_title == b"\x01\x02\x03\x04\x05\x06\x07\x08"

    def test_energy_registers_exist(self):
        reg = self.meter.get_object(2, (1, 0, 0, 0, 0, 255))
        assert reg is not None

    def test_simulate_reading(self):
        self.meter.simulate_reading(voltage=220.0, current=5.0)
        readings = self.meter.get_all_readings()
        assert readings["voltage_L1"] == 220.0
        assert readings["power_factor"] == 0.95
        assert readings["frequency"] == 50.0

    def test_energy_accumulates(self):
        self.meter.simulate_reading()
        v1 = self.meter.get_all_readings()["active_import"]
        self.meter.simulate_reading()
        v2 = self.meter.get_all_readings()["active_import"]
        # Energy should increase
        assert v2 >= v1

    def test_demand_tracking(self):
        self.meter.simulate_reading(voltage=220, current=10.0)  # ~2090W
        self.meter.simulate_reading(voltage=220, current=15.0)  # ~3135W
        self.meter.simulate_reading(voltage=220, current=5.0)   # ~1045W
        assert self.meter.demand_register.last_max_value is not None
        assert self.meter.demand_register.last_max_value > 1000

    def test_billing_profile_capture(self):
        for _ in range(5):
            self.meter.simulate_reading()
        assert self.meter.billing_profile.entries_in_use == 5
        assert len(self.meter.billing_profile.buffer) == 5

    def test_profile_range_read(self):
        for i in range(10):
            self.meter.simulate_reading()
        entries = self.meter.billing_profile.read_range(3, 7)
        assert len(entries) == 4

    def test_profile_overflow(self):
        self.meter.billing_profile.profile_entries = 5
        for _ in range(10):
            self.meter.simulate_reading()
        assert self.meter.billing_profile.entries_in_use == 5

    def test_load_profile_switch(self):
        idx = self.meter.profile_switch.add_profile("test", "1.0.99.3.0.255")
        self.meter.profile_switch.switch_profile(idx)
        assert self.meter.profile_switch.current_profile == idx
        assert self.meter.profile_switch.switch_time is not None

    def test_standard_events(self):
        self.meter.simulate_events()
        assert len(self.meter.standard_events.entries) > 0
        event = self.meter.standard_events.entries[0]
        assert event.event_name != "UNKNOWN_EVENT"

    def test_utility_events(self):
        self.meter.utility_events.register_event_code(1, "Custom event")
        self.meter.utility_events.add_event(1, event_data="test")
        assert len(self.meter.utility_events.entries) == 1
        assert self.meter.utility_events.entries[0].event_description == "Custom event"

    def test_event_notification(self):
        self.meter.event_notification.enable()
        self.meter.event_notification.event_list = [5, 6]
        result = self.meter.event_notification.notify(5, "power failure")
        assert result is not None
        assert self.meter.event_notification.notification_count == 1
        # Non-listed event should be ignored
        assert self.meter.event_notification.notify(99) is None

    def test_quality_control(self):
        assert self.meter.quality_control.is_valid()
        self.meter.quality_control.set_quality(
            QualityFlag.INVALID | QualityFlag.POWER_FAILURE,
            "Power failure detected"
        )
        assert not self.meter.quality_control.is_valid()
        assert self.meter.quality_control.has_flag(QualityFlag.INVALID)

    def test_interrogation(self):
        result = self.meter.interrogation.interrogate(level=1)
        assert isinstance(result, list)

    def test_gprs_setup(self):
        self.meter.gprs_setup.connect()
        assert self.meter.gprs_setup.is_connected()
        self.meter.gprs_setup.disconnect()
        assert not self.meter.gprs_setup.is_connected()

    def test_tcp_udp_setup(self):
        assert self.meter.tcp_setup.remote_port == 4059
        self.meter.tcp_setup.connect()
        assert self.meter.tcp_setup.status == 2

    def test_zigbee_setup(self):
        self.meter.zigbee_setup.join_network()
        assert self.meter.zigbee_setup.status == 1
        self.meter.zigbee_setup.leave_network()
        assert self.meter.zigbee_setup.status == 0

    def test_extended_register(self):
        from dlms_cosem.cosem.C3_ExtendedRegister import ExtendedRegister
        reg = ExtendedRegister(logical_name=Obis(a=0, b=0, c=96, d=1, e=0, f=255))
        reg.value = 12345
        from datetime import datetime
        reg.capture_time = datetime.now()
        assert reg.value == 12345
        reg.reset()
        assert reg.value == 0

    def test_value_with_register(self):
        from dlms_cosem.cosem.value_with_register import ValueWithRegister
        reg = ValueWithRegister(logical_name=Obis(a=0, b=0, c=96, d=2, e=0, f=255))
        reg.value = 100.0
        reg.register = 50000.0
        assert reg.value == 100.0
        assert reg.register == 50000.0
        reg.reset()
        assert reg.value == 0

    def test_profile_type_enums(self):
        from dlms_cosem.cosem.C5_ProfileGeneric import ProfileType, SortMethod, BufferOverflow
        assert ProfileType.LOAD_PROFILE == 0
        assert ProfileType.BILLING == 1
        assert SortMethod.FIFO == 1
        assert BufferOverflow.OVERWRITE_OLDEST == 2

    def test_profile_sort(self):
        self.meter.billing_profile.buffer = [[3], [1], [2]]
        self.meter.billing_profile.sort_method = SortMethod.LARGEST
        self.meter.billing_profile.sort_buffer()
        assert self.meter.billing_profile.buffer == [[3], [2], [1]]

    def test_event_filter(self):
        log = self.meter.standard_events
        log.event_filter = 0x0001  # only event code 1
        log.add_event(1)
        log.add_event(2)
        assert len(log.entries) == 1
        assert log.entries[0].event_code == 1

    def test_full_readings(self):
        self.meter.simulate_reading()
        readings = self.meter.get_all_readings()
        assert "active_import" in readings
        assert "voltage_L1" in readings
        assert "max_demand" in readings


# Import needed for test
from dlms_cosem.cosem.quality_control import QualityFlag
from dlms_cosem.cosem.C5_ProfileGeneric import SortMethod
