"""Tests for newly added COSEM IC classes."""
import pytest

from dlms_cosem import enumerations as enums
from dlms_cosem.cosem.obis import Obis
from dlms_cosem.cosem.C40_IPv4Setup import IPv4Setup
from dlms_cosem.cosem.C27_GPRSSetup import GPRSSetup, GprsModemSetup
from dlms_cosem.cosem.C15_PushSetup import PushSetup
from dlms_cosem.cosem.C16_DisconnectControl import DisconnectControl, DisconnectState
from dlms_cosem.cosem.C17_Limiter import Limiter
from dlms_cosem.cosem.C26_MBusClient import MBusClient
from dlms_cosem.cosem.C79_ParameterMonitor import ParameterMonitor
from dlms_cosem.cosem.C57_SensorManager import SensorManager
from dlms_cosem.cosem.C87_NTPSetup import NTPSetup
from dlms_cosem.cosem.C22_Account import Account
from dlms_cosem.cosem.C66_Credit import Credit
from dlms_cosem.cosem.C67_Charge import Charge
from dlms_cosem.cosem.C82_Arbitrator import Arbitrator
from dlms_cosem.cosem.C117_MACAddressSetup import MACAddressSetup
from dlms_cosem.cosem.C45_PPPSetup import PPPSetup, PPPAuthProtocol
from dlms_cosem.cosem.C28_SMTPSetup import SMTPSetup


OBIS = Obis.from_string("0.0.1.0.0.255")


class TestIPv4Setup:
    """Test IC42 IPv4 Setup."""

    def test_create(self):
        """Test creating IPv4 Setup object."""
        ipv4 = IPv4Setup(logical_name=OBIS)
        assert ipv4.CLASS_ID == enums.CosemInterface.IPV4_SETUP
        assert ipv4.ip_address == (0, 0, 0, 0)
        assert ipv4.dhcp_enabled is False

    def test_set_ip_address(self):
        """Test setting IP address."""
        ipv4 = IPv4Setup(
            logical_name=OBIS,
            ip_address=(192, 168, 1, 100),
            subnet_mask=(255, 255, 255, 0),
            gateway=(192, 168, 1, 1)
        )
        assert ipv4.ip_address == (192, 168, 1, 100)
        assert ipv4.get_ip_string() == "192.168.1.100"
        assert ipv4.get_subnet_string() == "255.255.255.0"

    def test_reset(self):
        """Test resetting IPv4 configuration."""
        ipv4 = IPv4Setup(
            logical_name=OBIS,
            ip_address=(10, 0, 0, 1),
            dhcp_enabled=True
        )
        ipv4.reset()
        assert ipv4.ip_address == (0, 0, 0, 0)
        assert ipv4.dhcp_enabled is False

    def test_static_attribute(self):
        """Test static attribute detection."""
        ipv4 = IPv4Setup(logical_name=OBIS)
        assert ipv4.is_static_attribute(1) is True
        assert ipv4.is_static_attribute(2) is False

    def test_dns_configuration(self):
        """Test DNS configuration."""
        ipv4 = IPv4Setup(
            logical_name=OBIS,
            primary_dns=(8, 8, 8, 8),
            secondary_dns=(8, 8, 4, 4)
        )
        assert ipv4.primary_dns == (8, 8, 8, 8)
        assert ipv4.secondary_dns == (8, 8, 4, 4)


class TestGPRSSetup:
    """Test IC45 GPRS Modem Setup."""

    def test_create(self):
        """Test creating GPRS Setup object."""
        gprs = GPRSSetup(logical_name=OBIS)
        assert gprs.CLASS_ID == enums.CosemInterface.GPRS_MODEM_SETUP
        assert gprs.apn == ""

    def test_configure_apn(self):
        """Test configuring APN."""
        gprs = GPRSSetup(
            logical_name=OBIS,
            apn="internet.provider.com",
            pin_code="1234"
        )
        assert gprs.apn == "internet.provider.com"
        assert gprs.pin_code == "1234"

    def test_reset(self):
        """Test resetting GPRS configuration."""
        gprs = GPRSSetup(logical_name=OBIS, apn="test.com")
        gprs.reset()
        assert gprs.apn == ""

    def test_alias_compatibility(self):
        """Test GprsModemSetup alias."""
        gprs = GprsModemSetup(logical_name=OBIS)
        assert isinstance(gprs, GPRSSetup)

    def test_authentication(self):
        """Test authentication settings."""
        gprs = GPRSSetup(
            logical_name=OBIS,
            username="user",
            password="pass"
        )
        assert gprs.username == "user"
        assert gprs.password == "pass"


class TestPushSetup:
    """Test IC40 Push Setup."""

    def test_create(self):
        """Test creating Push Setup object."""
        push = PushSetup(logical_name=OBIS)
        assert push.CLASS_ID == enums.CosemInterface.PUSH
        assert push.push_object_list == []

    def test_add_push_object(self):
        """Test adding objects to push list."""
        push = PushSetup(logical_name=OBIS)
        obis_voltage = Obis(1, 0, 32, 7, 0, 255)
        push.add_push_object(class_id=3, obis=obis_voltage, attribute_id=2)
        assert len(push.push_object_list) == 1
        assert push.push_object_list[0]["class_id"] == 3

    def test_reset(self):
        """Test resetting push configuration."""
        push = PushSetup(logical_name=OBIS)
        push.add_push_object(class_id=1, obis=OBIS, attribute_id=2)
        push.reset()
        assert push.push_object_list == []

    def test_retry_settings(self):
        """Test retry configuration."""
        push = PushSetup(
            logical_name=OBIS,
            number_of_retries=5,
            repetition_delay=120
        )
        assert push.number_of_retries == 5
        assert push.repetition_delay == 120

    def test_communication_window(self):
        """Test communication window configuration."""
        push = PushSetup(logical_name=OBIS)
        window = {"start": "00:00", "end": "06:00"}
        push.communication_window.append(window)
        assert len(push.communication_window) == 1


class TestDisconnectControl:
    """Test IC70 Disconnect Control."""

    def test_create(self):
        """Test creating Disconnect Control object."""
        dc = DisconnectControl(logical_name=OBIS)
        assert dc.CLASS_ID == enums.CosemInterface.DISCONNECT_CONTROL
        assert dc.is_connected() is True

    def test_remote_disconnect(self):
        """Test remote disconnect."""
        dc = DisconnectControl(logical_name=OBIS)
        dc.remote_disconnect()
        assert dc.is_disconnected() is True
        assert dc.output_state == DisconnectState.DISCONNECTED

    def test_remote_reconnect(self):
        """Test remote reconnect."""
        dc = DisconnectControl(logical_name=OBIS)
        dc.remote_disconnect()
        dc.control_state = DisconnectState.READY_FOR_RECONNECTION
        dc.remote_reconnect()
        assert dc.is_connected() is True

    def test_control_mode(self):
        """Test control mode configuration."""
        dc = DisconnectControl(logical_name=OBIS, control_mode=1)
        assert dc.control_mode == 1

    def test_static_attribute(self):
        """Test static attribute detection."""
        dc = DisconnectControl(logical_name=OBIS)
        assert dc.is_static_attribute(1) is True
        assert dc.is_static_attribute(2) is False


class TestLimiter:
    """Test IC71 Limiter."""

    def test_create(self):
        """Test creating Limiter object."""
        limiter = Limiter(logical_name=OBIS)
        assert limiter.CLASS_ID == enums.CosemInterface.LIMITER
        assert limiter.threshold_active == 0.0

    def test_threshold_checking(self):
        """Test threshold checking."""
        limiter = Limiter(
            logical_name=OBIS,
            threshold_active=100.0,
            threshold_normal=80.0
        )
        assert limiter.is_over_threshold(150.0) is True
        assert limiter.is_over_threshold(50.0) is False
        assert limiter.is_under_threshold(70.0) is True

    def test_reset(self):
        """Test resetting limiter."""
        limiter = Limiter(
            logical_name=OBIS,
            threshold_active=100.0
        )
        limiter.reset()
        assert limiter.threshold_active == 0.0

    def test_emergency_profile(self):
        """Test emergency profile configuration."""
        limiter = Limiter(
            logical_name=OBIS,
            emergency_profile_active=True,
            emergency_profile_group=5
        )
        assert limiter.emergency_profile_active is True
        assert limiter.emergency_profile_group == 5

    def test_duration_settings(self):
        """Test duration configuration."""
        limiter = Limiter(
            logical_name=OBIS,
            min_over_threshold_duration=60,
            min_under_threshold_duration=30
        )
        assert limiter.min_over_threshold_duration == 60
        assert limiter.min_under_threshold_duration == 30


class TestMBusClient:
    """Test IC72 M-Bus Client."""

    def test_create(self):
        """Test creating M-Bus Client object."""
        mbus = MBusClient(logical_name=OBIS)
        assert mbus.CLASS_ID == enums.CosemInterface.MBUS_CLIENT
        assert mbus.primary_addresses == []

    def test_capture(self):
        """Test capture method."""
        mbus = MBusClient(logical_name=OBIS)
        initial_access = mbus.access_number
        mbus.capture()
        assert mbus.access_number == initial_access + 1

    def test_reset(self):
        """Test resetting M-Bus client."""
        mbus = MBusClient(
            logical_name=OBIS,
            capture_period=3600,
            status=1
        )
        mbus.reset()
        assert mbus.capture_period == 0
        assert mbus.status == 0

    def test_device_info(self):
        """Test device information."""
        mbus = MBusClient(
            logical_name=OBIS,
            identification_number="12345678",
            manufacturer_id="ABC",
            version=1,
            device_type=2
        )
        assert mbus.identification_number == "12345678"
        assert mbus.manufacturer_id == "ABC"

    def test_primary_addresses(self):
        """Test primary address list."""
        mbus = MBusClient(logical_name=OBIS)
        mbus.primary_addresses = [1, 2, 3, 5, 10]
        assert len(mbus.primary_addresses) == 5


class TestParameterMonitor:
    """Test IC65 Parameter Monitor."""

    def test_create(self):
        """Test creating Parameter Monitor object."""
        pm = ParameterMonitor(logical_name=OBIS)
        assert pm.CLASS_ID == enums.CosemInterface.PARAMETER_MONITOR
        assert pm.parameter_list == []

    def test_add_parameter(self):
        """Test adding parameters to monitor."""
        pm = ParameterMonitor(logical_name=OBIS)
        obis_voltage = Obis(1, 0, 32, 7, 0, 255)
        pm.add_parameter(class_id=3, obis=obis_voltage, attribute_id=2)
        assert len(pm.parameter_list) == 1

    def test_reset(self):
        """Test resetting parameter monitor."""
        pm = ParameterMonitor(logical_name=OBIS)
        pm.add_parameter(class_id=1, obis=OBIS, attribute_id=2)
        pm.parameter_value = [42]
        pm.reset()
        assert pm.parameter_value == []
        assert pm.changed_parameter is None

    def test_parameter_values(self):
        """Test parameter values."""
        pm = ParameterMonitor(logical_name=OBIS)
        pm.parameter_value = [100, 200, 300]
        assert len(pm.parameter_value) == 3


class TestSensorManager:
    """Test IC67 Sensor Manager."""

    def test_create(self):
        """Test creating Sensor Manager object."""
        sm = SensorManager(logical_name=OBIS)
        assert sm.CLASS_ID == enums.CosemInterface.SENSOR_MANAGER
        assert sm.sensor_list == []

    def test_add_sensor(self):
        """Test adding sensors."""
        sm = SensorManager(logical_name=OBIS)
        obis_sensor = Obis(1, 0, 1, 8, 0, 255)
        sm.add_sensor(sensor_obis=obis_sensor, sensor_type=1)
        assert len(sm.sensor_list) == 1
        assert len(sm.sensor_status) == 1

    def test_reset(self):
        """Test resetting sensor manager."""
        sm = SensorManager(logical_name=OBIS)
        obis_sensor = Obis(1, 0, 1, 8, 0, 255)
        sm.add_sensor(sensor_obis=obis_sensor, sensor_type=1)
        sm.totals = [100.0]
        sm.reset()
        assert sm.sensor_status == []
        assert sm.totals == []

    def test_sensor_status(self):
        """Test sensor status tracking."""
        sm = SensorManager(logical_name=OBIS)
        sm.sensor_status = [0, 1, 0]
        assert len(sm.sensor_status) == 3


class TestNTPSetup:
    """Test IC100 NTP Setup."""

    def test_create(self):
        """Test creating NTP Setup object."""
        ntp = NTPSetup(logical_name=OBIS)
        assert ntp.CLASS_ID == enums.CosemInterface.NTP_SETUP
        assert ntp.ntp_enabled is False

    def test_add_server(self):
        """Test adding NTP server."""
        ntp = NTPSetup(logical_name=OBIS)
        ntp.add_server("pool.ntp.org")
        ntp.add_server("time.google.com")
        assert len(ntp.ntp_servers) == 2

    def test_reset(self):
        """Test resetting NTP configuration."""
        ntp = NTPSetup(
            logical_name=OBIS,
            ntp_enabled=True,
            ntp_servers=["pool.ntp.org"]
        )
        ntp.reset()
        assert ntp.ntp_enabled is False
        assert ntp.ntp_servers == []

    def test_sync_now(self):
        """Test sync_now method."""
        ntp = NTPSetup(logical_name=OBIS)
        ntp.sync_now()  # Should not raise

    def test_poll_interval(self):
        """Test poll interval configuration."""
        ntp = NTPSetup(
            logical_name=OBIS,
            ntp_poll_interval=7200,
            ntp_port=123
        )
        assert ntp.ntp_poll_interval == 7200
        assert ntp.ntp_port == 123


class TestAccount:
    """Test IC111 Account."""

    def test_create(self):
        """Test creating Account object."""
        account = Account(logical_name=OBIS)
        assert account.CLASS_ID == enums.CosemInterface.ACCOUNT
        assert account.current_credit_amount == 0.0

    def test_credit_management(self):
        """Test credit management."""
        account = Account(
            logical_name=OBIS,
            current_credit_amount=100.0,
            available_credit=100.0
        )
        assert account.has_sufficient_credit(50.0) is True
        assert account.has_sufficient_credit(150.0) is False

    def test_use_credit(self):
        """Test using credit."""
        account = Account(
            logical_name=OBIS,
            available_credit=100.0,
            credit_in_use=0.0
        )
        result = account.use_credit(30.0)
        assert result is True
        assert account.available_credit == 70.0
        assert account.credit_in_use == 30.0

    def test_reset(self):
        """Test resetting account."""
        account = Account(
            logical_name=OBIS,
            current_credit_amount=100.0,
            current_debit_amount=50.0
        )
        account.reset()
        assert account.current_credit_amount == 0.0
        assert account.current_debit_amount == 0.0

    def test_emergency_credit(self):
        """Test emergency credit configuration."""
        account = Account(
            logical_name=OBIS,
            emergency_credit_limit=20.0,
            emergency_credit_threshold=5.0
        )
        assert account.emergency_credit_limit == 20.0


class TestCredit:
    """Test IC112 Credit."""

    def test_create(self):
        """Test creating Credit object."""
        credit = Credit(logical_name=OBIS)
        assert credit.CLASS_ID == enums.CosemInterface.CREDIT
        assert credit.current_credit_amount == 0.0

    def test_update_credit_amount(self):
        """Test updating credit amount."""
        credit = Credit(logical_name=OBIS, current_credit_amount=50.0)
        credit.update_credit_amount(25.0)
        assert credit.current_credit_amount == 75.0

    def test_low_credit_warning(self):
        """Test low credit warning."""
        credit = Credit(
            logical_name=OBIS,
            current_credit_amount=10.0,
            warning_threshold=20.0
        )
        assert credit.is_low_credit() is True

    def test_reset(self):
        """Test resetting credit."""
        credit = Credit(logical_name=OBIS, current_credit_amount=100.0)
        credit.reset()
        assert credit.current_credit_amount == 0.0

    def test_credit_available(self):
        """Test checking if credit is available."""
        credit = Credit(logical_name=OBIS, current_credit_amount=50.0)
        assert credit.is_credit_available() is True
        credit.current_credit_amount = 0.0
        assert credit.is_credit_available() is False


class TestCharge:
    """Test IC113 Charge."""

    def test_create(self):
        """Test creating Charge object."""
        charge = Charge(logical_name=OBIS)
        assert charge.CLASS_ID == enums.CosemInterface.CHARGE
        assert charge.total_amount == 0.0

    def test_update_total_amount(self):
        """Test updating total charge amount."""
        charge = Charge(logical_name=OBIS, total_amount=10.0)
        charge.update_total_amount(5.0)
        assert charge.total_amount == 15.0

    def test_calculate_charge(self):
        """Test calculating charge."""
        charge = Charge(
            logical_name=OBIS,
            unit_charge_active=0.15
        )
        amount = charge.calculate_charge(100.0)
        assert amount == 15.0

    def test_reset(self):
        """Test resetting charge."""
        charge = Charge(logical_name=OBIS, total_amount=100.0)
        charge.reset()
        assert charge.total_amount == 0.0

    def test_charge_configuration(self):
        """Test charge configuration."""
        charge = Charge(
            logical_name=OBIS,
            charge_type=1,
            priority=2,
            unit_charge=0.10,
            unit_charge_active=0.10
        )
        assert charge.charge_type == 1
        assert charge.priority == 2


class TestArbitrator:
    """Test IC68 Arbitrator."""

    def test_create(self):
        """Test creating Arbitrator object."""
        arb = Arbitrator(logical_name=OBIS)
        assert arb.CLASS_ID == enums.CosemInterface.ARBITRATOR
        assert arb.active_controls == []

    def test_activate_control(self):
        """Test activating control."""
        arb = Arbitrator(logical_name=OBIS)
        arb.activate_control(1)
        arb.activate_control(2)
        assert 1 in arb.active_controls
        assert 2 in arb.active_controls

    def test_deactivate_control(self):
        """Test deactivating control."""
        arb = Arbitrator(logical_name=OBIS)
        arb.activate_control(1)
        arb.deactivate_control(1)
        assert 1 not in arb.active_controls

    def test_reset(self):
        """Test resetting arbitrator."""
        arb = Arbitrator(logical_name=OBIS)
        arb.activate_control(1)
        arb.activate_control(2)
        arb.reset()
        assert arb.active_controls == []

    def test_permissions(self):
        """Test permissions configuration."""
        arb = Arbitrator(logical_name=OBIS)
        arb.permissions = [1, 2, 3]
        assert len(arb.permissions) == 3


class TestMACAddressSetup:
    """Test IC43 MAC Address Setup."""

    def test_create(self):
        """Test creating MAC Address Setup object."""
        mac = MACAddressSetup(logical_name=OBIS)
        assert mac.CLASS_ID == enums.CosemInterface.MAC_ADDRESS_SETUP
        assert mac.mac_address == (0, 0, 0, 0, 0, 0)

    def test_set_mac_address(self):
        """Test setting MAC address."""
        mac = MACAddressSetup(
            logical_name=OBIS,
            mac_address=(0xAA, 0xBB, 0xCC, 0xDD, 0xEE, 0xFF)
        )
        assert mac.mac_address == (0xAA, 0xBB, 0xCC, 0xDD, 0xEE, 0xFF)
        assert mac.get_mac_string() == "AA:BB:CC:DD:EE:FF"

    def test_set_mac_from_string(self):
        """Test setting MAC from string."""
        mac = MACAddressSetup(logical_name=OBIS)
        mac.set_mac_from_string("DE:AD:BE:EF:CA:FE")
        assert mac.mac_address == (0xDE, 0xAD, 0xBE, 0xEF, 0xCA, 0xFE)

    def test_reset(self):
        """Test resetting MAC address."""
        mac = MACAddressSetup(
            logical_name=OBIS,
            mac_address=(0x11, 0x22, 0x33, 0x44, 0x55, 0x66)
        )
        mac.reset()
        assert mac.mac_address == (0, 0, 0, 0, 0, 0)


class TestPPPSetup:
    """Test IC44 PPP Setup."""

    def test_create(self):
        """Test creating PPP Setup object."""
        ppp = PPPSetup(logical_name=OBIS)
        assert ppp.CLASS_ID == enums.CosemInterface.PPP_SETUP
        assert ppp.username == ""

    def test_configure_authentication(self):
        """Test configuring authentication."""
        ppp = PPPSetup(
            logical_name=OBIS,
            username="user123",
            password="pass456",
            authentication_protocol=PPPAuthProtocol.PAP
        )
        assert ppp.username == "user123"
        assert ppp.authentication_protocol == PPPAuthProtocol.PAP

    def test_reset(self):
        """Test resetting PPP configuration."""
        ppp = PPPSetup(
            logical_name=OBIS,
            username="test",
            local_ip="192.168.1.1"
        )
        ppp.reset()
        assert ppp.username == ""
        assert ppp.local_ip == "0.0.0.0"

    def test_ip_configuration(self):
        """Test IP configuration."""
        ppp = PPPSetup(
            logical_name=OBIS,
            local_ip="10.0.0.1",
            remote_ip="10.0.0.2",
            dns_primary="8.8.8.8",
            dns_secondary="8.8.4.4"
        )
        assert ppp.local_ip == "10.0.0.1"
        assert ppp.dns_primary == "8.8.8.8"

    def test_idle_timeout(self):
        """Test idle timeout configuration."""
        ppp = PPPSetup(logical_name=OBIS, idle_timeout=300)
        assert ppp.idle_timeout == 300


class TestSMTPSetup:
    """Test IC46 SMTP Setup."""

    def test_create(self):
        """Test creating SMTP Setup object."""
        smtp = SMTPSetup(logical_name=OBIS)
        assert smtp.CLASS_ID == enums.CosemInterface.SMTP_SETUP
        assert smtp.server_address == ""

    def test_configure_server(self):
        """Test configuring SMTP server."""
        smtp = SMTPSetup(
            logical_name=OBIS,
            server_address="smtp.example.com",
            server_port=587,
            use_tls=True
        )
        assert smtp.server_address == "smtp.example.com"
        assert smtp.server_port == 587
        assert smtp.use_tls is True

    def test_add_recipient(self):
        """Test adding recipients."""
        smtp = SMTPSetup(logical_name=OBIS)
        smtp.add_recipient("user1@example.com")
        smtp.add_recipient("user2@example.com")
        assert len(smtp.recipient_list) == 2

    def test_reset(self):
        """Test resetting SMTP configuration."""
        smtp = SMTPSetup(
            logical_name=OBIS,
            server_address="smtp.test.com",
            sender_address="sender@test.com"
        )
        smtp.reset()
        assert smtp.server_address == ""
        assert smtp.sender_address == ""

    def test_send_test_email(self):
        """Test send_test_email method."""
        smtp = SMTPSetup(
            logical_name=OBIS,
            server_address="smtp.example.com"
        )
        smtp.add_recipient("user@example.com")
        result = smtp.send_test_email()
        assert result is True

    def test_authentication(self):
        """Test SMTP authentication."""
        smtp = SMTPSetup(
            logical_name=OBIS,
            username="smtp_user",
            password="smtp_pass"
        )
        assert smtp.username == "smtp_user"
        assert smtp.password == "smtp_pass"
