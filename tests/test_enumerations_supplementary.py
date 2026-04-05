from dlms_cosem import enumerations as enums


class TestCosemInterface:
    def test_data(self):
        assert enums.CosemInterface.DATA == 1

    def test_register(self):
        assert enums.CosemInterface.REGISTER == 2

    def test_extended_register(self):
        assert enums.CosemInterface.EXTENDED_REGISTER == 3

    def test_demand_register(self):
        assert enums.CosemInterface.DEMAND_REGISTER == 4

    def test_profile_generic(self):
        assert enums.CosemInterface.PROFILE_GENERIC == 5

    def test_clock(self):
        assert enums.CosemInterface.CLOCK == 6

    def test_script_table(self):
        assert enums.CosemInterface.SCRIPT_TABLE == 7

    def test_special_days_table(self):
        assert enums.CosemInterface.SPECIAL_DAYS_TABLE == 8

    def test_schedule(self):
        assert enums.CosemInterface.SCHEDULE == 9

    def test_association_sn(self):
        assert enums.CosemInterface.ASSOCIATION_SN == 10

    def test_association_ln(self):
        assert enums.CosemInterface.ASSOCIATION_LN == 11

    def test_iec_local_port_setup(self):
        assert enums.CosemInterface.IEC_LOCAL_PORT_SETUP == 102  # alias for INFRARED_SETUP

    def test_image_transfer(self):
        assert enums.CosemInterface.IMAGE_TRANSFER == 35

    def test_security_setup(self):
        assert enums.CosemInterface.SECURITY_SETUP == 29

    def test_push(self):
        assert enums.CosemInterface.PUSH == 15  # alias for PUSH_SETUP

    def test_tcp_udp_setup(self):
        assert enums.CosemInterface.TCP_UDP_SETUP == 39

    def test_register_table(self):
        assert enums.CosemInterface.REGISTER_TABLE == 61  # alias for ACTUATOR

    def test_utility_tables(self):
        assert enums.CosemInterface.UTILITY_TABLES == 121

    def test_auto_answer(self):
        assert enums.CosemInterface.AUTO_ANSWER == 28  # alias for SMTP_SETUP

    def test_auto_connect(self):
        assert enums.CosemInterface.AUTO_CONNECT == 48

    def test_value_table(self):
        assert enums.CosemInterface.VALUE_TABLE == 119

    def test_iec_public_key(self):
        assert enums.CosemInterface.IEC_PUBLIC_KEY == 32

    def test_mbus_diagnostic(self):
        assert enums.CosemInterface.MBUS_DIAGNOSTIC == 83

    def test_power_quality_monitor(self):
        assert enums.CosemInterface.POWER_QUALITY_MONITOR == 110

    def test_harmonic_monitor(self):
        assert enums.CosemInterface.HARMONIC_MONITOR == 111

    def test_sag_swell_monitor(self):
        assert enums.CosemInterface.SAG_SWELL_MONITOR == 112

    def test_iec_hdlc_setup(self):
        assert enums.CosemInterface.IEC_HDLC_SETUP == 23

    def test_iec_twisted_pair_setup(self):
        assert enums.CosemInterface.IEC_TWISTED_PAIR_SETUP == 101  # alias for RS485_SETUP

    def test_modem_configuration(self):
        assert enums.CosemInterface.MODEM_CONFIGURATION == 24

    def test_register_monitor(self):
        assert enums.CosemInterface.REGISTER_MONITOR == 13

    def test_single_action_schedule(self):
        assert enums.CosemInterface.SINGLE_ACTION_SCHEDULE == 71

    def test_disconnect_control(self):
        assert enums.CosemInterface.DISCONNECT_CONTROL == 16

    def test_limiter(self):
        assert enums.CosemInterface.LIMITER == 17

    def test_parameter_monitor(self):
        assert enums.CosemInterface.PARAMETER_MONITOR == 79

    def test_sensor_manager(self):
        assert enums.CosemInterface.SENSOR_MANAGER == 57

    def test_arbitrator(self):
        assert enums.CosemInterface.ARBITRATOR == 82

    def test_gprs_modem_setup(self):
        assert enums.CosemInterface.GPRS_MODEM_SETUP == 27

    def test_ipv4_setup(self):
        assert enums.CosemInterface.IPV4_SETUP == 40

    def test_ipv6_setup(self):
        assert enums.CosemInterface.IPV6_SETUP == 43

    def test_mbus_client(self):
        assert enums.CosemInterface.MBUS_CLIENT == 26

    def test_ntp_setup(self):
        assert enums.CosemInterface.NTP_SETUP == 87
