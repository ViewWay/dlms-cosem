"""Supplementary tests for enumerations and constants."""
import pytest
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from dlms_cosem import enumerations as enums


class TestCosemInterface:
    def test_data_class(self):
        assert enums.CosemInterface.DATA == 1

    def test_register_class(self):
        assert enums.CosemInterface.REGISTER == 3

    def test_extended_register(self):
        assert enums.CosemInterface.EXTENDED_REGISTER == 4

    def test_demand_register(self):
        assert enums.CosemInterface.DEMAND_REGISTER == 5

    def test_register_activation(self):
        assert enums.CosemInterface.REGISTER_ACTIVATION == 6

    def test_profile_generic(self):
        assert enums.CosemInterface.PROFILE_GENERIC == 7

    def test_clock(self):
        assert enums.CosemInterface.CLOCK == 8

    def test_script_table(self):
        assert enums.CosemInterface.SCRIPT_TABLE == 9

    def test_schedule(self):
        assert enums.CosemInterface.SCHEDULE == 10

    def test_special_days(self):
        assert enums.CosemInterface.SPECIAL_DAYS_TABLE == 11

    def test_association_sn(self):
        assert enums.CosemInterface.ASSOCIATION_SN == 12

    def test_association_ln(self):
        assert enums.CosemInterface.ASSOCIATION_LN == 15

    def test_local_port_setup(self):
        assert enums.CosemInterface.IEC_LOCAL_PORT_SETUP == 19

    def test_image_transfer(self):
        assert enums.CosemInterface.IMAGE_TRANSFER == 18

    def test_security_setup(self):
        assert enums.CosemInterface.SECURITY_SETUP == 64

    def test_push(self):
        assert enums.CosemInterface.PUSH == 40

    def test_tcp_udp_setup(self):
        assert enums.CosemInterface.TCP_UDP_SETUP == 41

    def test_register_table(self):
        assert enums.CosemInterface.REGISTER_TABLE == 61

    def test_utility_tables(self):
        assert enums.CosemInterface.UTILITY_TABLES == 26

    def test_auto_answer(self):
        assert enums.CosemInterface.AUTO_ANSWER == 28

    def test_auto_connect(self):
        assert enums.CosemInterface.AUTO_CONNECT == 29

    def test_iec_hdlc_setup(self):
        assert enums.CosemInterface.IEC_HDLC_SETUP == 23

    def test_iec_twisted_pair_setup(self):
        assert enums.CosemInterface.IEC_TWISTED_PAIR_SETUP == 24

    def test_modem_configuration(self):
        assert enums.CosemInterface.MODEM_CONFIGURATION == 27

    def test_register_monitor(self):
        assert enums.CosemInterface.REGISTER_MONITOR == 21

    def test_single_action_schedule(self):
        assert enums.CosemInterface.SINGLE_ACTION_SCHEDULE == 22

    def test_disconnect_control(self):
        assert enums.CosemInterface.DISCONNECT_CONTROL == 70

    def test_limiter(self):
        assert enums.CosemInterface.LIMITER == 71

    def test_parameter_monitor(self):
        assert enums.CosemInterface.PARAMETER_MONITOR == 65

    def test_sensor_manager(self):
        assert enums.CosemInterface.SENSOR_MANAGER == 67

    def test_arbitrator(self):
        assert enums.CosemInterface.ARBITRATOR == 68

    def test_gprs_modem_setup(self):
        assert enums.CosemInterface.GPRS_MODEM_SETUP == 45

    def test_ipv4_setup(self):
        assert enums.CosemInterface.IPV4_SETUP == 42

    def test_ipv6_setup(self):
        assert enums.CosemInterface.IPV6_SETUP == 48

    def test_mbuss_client(self):
        assert enums.CosemInterface.MBUS_CLIENT == 72

    def test_ntp_setup(self):
        assert enums.CosemInterface.NTP_SETUP == 100


class TestCosemInterfaceEnumProperties:
    def test_all_positive(self):
        for member in enums.CosemInterface:
            assert member.value > 0, f"{member.name} has non-positive value"

    def test_no_duplicates(self):
        values = [m.value for m in enums.CosemInterface]
        assert len(values) == len(set(values)), "Duplicate enum values found"

    def test_is_int_enum(self):
        assert issubclass(enums.CosemInterface, int)
