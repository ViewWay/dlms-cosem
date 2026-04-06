#!/usr/bin/env python3
"""Generate all missing COSEM IC class files for Blue Book Ed.16."""

import os

BASE_DIR = "/Users/yimiliya/.openclaw/workspace/dlms-cosem/dlms_cosem/cosem"

# Each entry: (filename, class_name, class_id, version, enum_name, docstring, attributes_list)
# attributes_list: list of (attr_id, attr_name, default_factory)
# Methods: list of (method_id, method_name)

CLASSES = [
    # === Data Storage ===
    ("C26_UtilityTables.py", "UtilityTables", 26, 0, "UTILITY_TABLES",
     "Utility Tables - stores table cell values for utility data.",
     [(1, "logical_name", "Obis"), (2, "table_cell_values", "list")],
     []),

    ("C66_MeasurementDataMonitoring.py", "MeasurementDataMonitoring", 66, 0, "MEASUREMENT_DATA_MONITORING",
     "Measurement Data Monitoring - monitors measurement data with trigger-based capture.",
     [(1, "logical_name", "Obis"), (2, "status", "int", 0), (3, "trigger_source", "int", 0),
      (4, "sampling_rate", "int", 0), (5, "number_of_samples_before_trigger", "int", 0),
      (6, "number_of_samples_after_trigger", "int", 0), (7, "trigger_time", "bytes", None),
      (8, "scaler_unit", "object", None)],
     [(1, "reset"), (2, "capture")]),

    # === Auto Connect ===
    ("C29_AutoConnect.py", "AutoConnect", 29, 2, "AUTO_CONNECT",
     "Auto Connect - manages automatic connection establishment.",
     [(1, "logical_name", "Obis"), (2, "mode", "int", 0), (3, "repetitions", "int", 0),
      (4, "repetition_delay", "int", 0), (5, "calling_window", "list", None),
      (6, "allowed_destinations", "list", None)],
     [(1, "set_mode")]),

    # === GSM Diagnostic ===
    ("C47_GSMDiagnostic.py", "GSMDiagnostic", 47, 2, "GSM_DIAGNOSTICS",
     "GSM Diagnostic - provides GSM network diagnostic information.",
     [(1, "logical_name", "Obis"), (2, "operator", "str", ""), (3, "status", "int", 0),
      (4, "circuit_switch_status", "int", 0), (5, "packet_switch_status", "int", 0),
      (6, "cell_id", "int", 0), (7, "location_area", "int", 0),
      (8, "vci", "int", 0), (9, "mcc", "int", 0), (10, "mnc", "int", 0),
      (11, "base_station_id", "int", 0)],
     []),

    # === LTE Monitoring ===
    ("C151_LTEMonitoring.py", "LTEMonitoring", 151, 1, "LTE_MONITORING",
     "LTE Monitoring - provides LTE network monitoring information.",
     [(1, "logical_name", "Obis"), (2, "operator", "str", ""), (3, "signal_strength", "int", 0),
      (4, "noise_level", "int", 0), (5, "status", "int", 0),
      (6, "circuit_switch_status", "int", 0), (7, "packet_switch_status", "int", 0),
      (8, "cell_id", "int", 0), (9, "location_area", "int", 0),
      (10, "vci", "int", 0), (11, "mcc", "int", 0), (12, "mnc", "int", 0),
      (13, "base_station_id", "int", 0), (14, "sim_status", "int", 0),
      (15, "roaming_status", "int", 0)],
     []),

    # === M-Bus ===
    ("C25_MBusSlavePortSetup.py", "MBusSlavePortSetup", 25, 0, "MBUS_SLAVE_PORT_SETUP",
     "M-Bus Slave Port Setup - configuration for M-Bus slave port.",
     [(1, "logical_name", "Obis"), (2, "primary_address", "int", 0),
      (3, "identification_number", "int", 0), (4, "manufacturer_id", "int", 0),
      (5, "version", "int", 0), (6, "device_type", "int", 0),
      (7, "access_number", "int", 0), (8, "status", "int", 0),
      (9, "aligned", "bool", False)],
     []),

    ("C73_WirelessModeQChannel.py", "WirelessModeQChannel", 73, 1, "MBUS_WIRELESS_MODE_Q_CHANNEL",
     "Wireless Mode Q Channel - wireless M-Bus mode Q channel configuration.",
     [(1, "logical_name", "Obis"), (2, "channel_info", "list", None)],
     []),

    ("C74_MBusMasterPortSetup.py", "MBusMasterPortSetup", 74, 0, "MBUS_MASTER_PORT_SETUP",
     "M-Bus Master Port Setup - configuration for M-Bus master port.",
     [(1, "logical_name", "Obis"), (2, "comm_speed", "int", 0),
      (3, "rec_timeout", "int", 0), (4, "send_timeout", "int", 0)],
     []),

    ("C76_DLMSMBusPortSetup.py", "DLMSMBusPortSetup", 76, 0, "MBUS_PORT_SETUP_DLMS_COSEM_SERVER",
     "DLMS/COSEM Server M-Bus Port Setup - DLMS server on M-Bus port.",
     [(1, "logical_name", "Obis"), (2, "m_bus_port_reference", "str", ""),
      (3, "listen_port", "int", 0), (4, "slave_devices", "list", None),
      (5, "client_active", "bool", False)],
     [(1, "capture"), (2, "transfer"), (3, "synchronize_time"), (4, "initialize")]),

    # === IPv6 Setup ===
    ("C48_IPv6Setup.py", "IPv6Setup", 48, 0, "IPV6_SETUP",
     "IPv6 Setup - IPv6 address configuration.",
     [(1, "logical_name", "Obis"), (2, "address_configuration_mode", "int", 0),
      (3, "link_local_address", "bytes", None), (4, "address_list", "list", None)],
     []),

    # === CoAP ===
    ("C152_CoAPSetup.py", "CoAPSetup", 152, 0, "COAP_SETUP",
     "CoAP Setup - Constrained Application Protocol configuration.",
     [(1, "logical_name", "Obis"), (2, "coap_server_address", "str", ""),
      (3, "coap_server_port", "int", 0), (4, "response_timeout", "int", 0),
      (5, "max_retransmit", "int", 0), (6, "ack_timeout", "int", 0),
      (7, "ack_random_factor", "int", 0)],
     []),

    ("C153_CoAPDiagnostic.py", "CoAPDiagnostic", 153, 0, "COAP_DIAGNOSTICS",
     "CoAP Diagnostic - Constrained Application Protocol diagnostics.",
     [(1, "logical_name", "Obis"), (2, "messages_sent", "int", 0),
      (3, "messages_received", "int", 0), (4, "messages_failed", "int", 0),
      (5, "messages_retransmitted", "int", 0)],
     []),

    # === S-FSK PLC ===
    ("C50_SFSKPhyMACSetup.py", "SFSKPhyMACSetup", 50, 1, "S_FSK_PHY_MAC_SETUP",
     "S-FSK Phy&MAC Setup - S-FSK physical and MAC layer configuration.",
     [(1, "logical_name", "Obis"), (2, "mac_address", "bytes", None),
      (3, "phy_list", "list", None), (4, "tx_level", "int", 0),
      (5, "rx_level", "int", 0), (6, "frequency_band", "int", 0),
      (7, "data_rate", "int", 0), (8, "tx_frequency", "int", 0),
      (9, "rx_frequency", "int", 0)],
     []),

    ("C51_SFSKActiveInitiator.py", "SFSKActiveInitiator", 51, 0, "S_FSK_ACTIVE_INITIATOR",
     "S-FSK Active Initiator - manages S-FSK active initiator.",
     [(1, "logical_name", "Obis"), (2, "active_initiator", "list", None),
      (3, "active_initiator_count", "int", 0)],
     []),

    ("C52_SFSKMACSyncTimeouts.py", "SFSKMACSyncTimeouts", 52, 0, "S_FSK_MAC_SYNCHRONISATION_TIMEOUTS",
     "S-FSK MAC Synchronization Timeouts - S-FSK MAC sync timeout configuration.",
     [(1, "logical_name", "Obis"), (2, "time_outs", "list", None)],
     []),

    ("C53_SFSKMACCounters.py", "SFSKMACCounters", 53, 0, "S_FSK_MAC_COUNTERS",
     "S-FSK MAC Counters - S-FSK MAC layer counters.",
     [(1, "logical_name", "Obis"), (2, "tx_packet_count", "int", 0),
      (3, "rx_packet_count", "int", 0), (4, "crc_error_count", "int", 0),
      (5, "tx_time", "int", 0), (6, "rx_time", "int", 0)],
     []),

    ("C55_IEC61334LLCSetup.py", "IEC61334LLCSetup", 55, 1, "S_FSK_IEC_61334_4_32_LLC_SETUP",
     "IEC 61334-4-32 LLC Setup - LLC setup for IEC 61334-4-32.",
     [(1, "logical_name", "Obis"), (2, "llc_type_1_enable", "bool", False),
      (3, "llc_type_2_enable", "bool", False), (4, "llc_type_3_enable", "bool", False)],
     []),

    ("C56_SFSKReportingSystemList.py", "SFSKReportingSystemList", 56, 0, "S_FSK_REPORTING_SYSTEM_LIST",
     "S-FSK Reporting System List - list of S-FSK reporting systems.",
     [(1, "logical_name", "Obis"), (2, "reporting_system_list", "list", None)],
     []),

    # === LLC ===
    ("C57_LLCType1Setup.py", "LLCType1Setup", 57, 0, "IEC_8802_2_LLC_TYPE_1_SETUP",
     "IEC 8802-2 LLC Type 1 Setup - LLC Type 1 connectionless setup.",
     [(1, "logical_name", "Obis"), (2, "llc_type_1_enable", "bool", False),
      (3, "llc_type_1_parameters", "list", None)],
     []),

    ("C58_LLCType2Setup.py", "LLCType2Setup", 58, 0, "IEC_8802_2_LLC_TYPE_2_SETUP",
     "IEC 8802-2 LLC Type 2 Setup - LLC Type 2 connection-oriented setup.",
     [(1, "logical_name", "Obis"), (2, "llc_type_2_enable", "bool", False),
      (3, "llc_type_2_parameters", "list", None),
      (4, "llc_type_2_window_size", "int", 0), (5, "llc_type_2_retry_count", "int", 0)],
     []),

    ("C59_LLCType3Setup.py", "LLCType3Setup", 59, 0, "IEC_8802_2_LLC_TYPE_3_SETUP",
     "IEC 8802-2 LLC Type 3 Setup - LLC Type 3 acknowledged connectionless setup.",
     [(1, "logical_name", "Obis"), (2, "llc_type_3_enable", "bool", False),
      (3, "llc_type_3_parameters", "list", None),
      (4, "llc_type_3_window_size", "int", 0), (5, "llc_type_3_retry_count", "int", 0)],
     []),

    # === PRIME PLC ===
    ("C80_PRIMELLCSSCSSetup.py", "PRIMELLCSSCSSetup", 80, 0, "PRIME_61344_4_32_LLC_SSCS_SETUP",
     "PRIME 61334-4-32 LLC SSCS Setup - PRIME LLC SSCS configuration.",
     [(1, "logical_name", "Obis"), (2, "sscs_type", "int", 0),
      (3, "sscs_enable", "bool", False), (4, "sscs_response_time", "int", 0)],
     []),

    ("C81_PRIMEPhysicalCounters.py", "PRIMEPhysicalCounters", 81, 0, "PRIME_OFDM_PLC_PHYSICAL_LAYER_COUNTERS",
     "PRIME NB OFDM PLC Physical Layer Counters - PRIME PHY counters.",
     [(1, "logical_name", "Obis"), (2, "phy_tx_drop", "int", 0),
      (3, "phy_rx_total", "int", 0), (4, "phy_rx_crc_error", "int", 0),
      (5, "phy_tx_total", "int", 0)],
     []),

    ("C82_PRIMEMACSetup.py", "PRIMEMACSetup", 82, 0, "PRIME_OFDM_PLC_MAC_SETUP",
     "PRIME NB OFDM PLC MAC Setup - PRIME MAC configuration.",
     [(1, "logical_name", "Obis"), (2, "mac_address", "bytes", None),
      (3, "mac_frame_counter", "int", 0), (4, "mac_key", "bytes", None),
      (5, "mac_switch", "bool", False), (6, "mac_security_enabled", "bool", False),
      (7, "mac_security_level", "int", 0)],
     []),

    ("C83_PRIMEMACFuncParams.py", "PRIMEMACFuncParams", 83, 0, "PRIME_OFDM_PLC_MAC_FUNCTIONAL_PARAMETERS",
     "PRIME NB OFDM PLC MAC Functional Parameters - PRIME MAC functional params.",
     [(1, "logical_name", "Obis"), (2, "mac_address", "bytes", None),
      (3, "mac_frame_counter", "int", 0), (4, "mac_key", "bytes", None),
      (5, "mac_switch", "bool", False), (6, "mac_security_enabled", "bool", False),
      (7, "mac_security_level", "int", 0)],
     []),

    ("C84_PRIMEMACCounters.py", "PRIMEMACCounters", 84, 0, "PRIME_OFDM_PLC_MAC_COUNTERS",
     "PRIME NB OFDM PLC MAC Counters - PRIME MAC counters.",
     [(1, "logical_name", "Obis"), (2, "mac_tx_total", "int", 0),
      (3, "mac_rx_total", "int", 0), (4, "mac_tx_error", "int", 0),
      (5, "mac_rx_error", "int", 0), (6, "mac_tx_dropped", "int", 0),
      (7, "mac_rx_dropped", "int", 0)],
     []),

    ("C85_PRIMEMACNetworkAdmin.py", "PRIMEMACNetworkAdmin", 85, 0, "PRIME_OFDM_PLC_MAC_NETWORK_ADMINISTRATION_DATA",
     "PRIME NB OFDM PLC MAC Network Administration Data - PRIME network admin.",
     [(1, "logical_name", "Obis"), (2, "network_id", "int", 0),
      (3, "network_role", "int", 0), (4, "network_state", "int", 0),
      (5, "network_device_list", "list", None)],
     []),

    ("C86_PRIMEAppIdentification.py", "PRIMEAppIdentification", 86, 0, "PRIME_OFDM_PLC_MAC_APPLICATION_IDENTIFICATION",
     "PRIME NB OFDM PLC Application Identification - PRIME app identification.",
     [(1, "logical_name", "Obis"), (2, "application_name", "str", ""),
      (3, "application_version", "str", "")],
     []),

    # === G3-PLC ===
    ("C90_G3MACCounters.py", "G3MACCounters", 90, 1, "G3_PLC_MAC_LAYER_COUNTERS",
     "G3-PLC MAC Layer Counters - G3-PLC MAC layer counters.",
     [(1, "logical_name", "Obis"), (2, "mac_tx_packet_count", "int", 0),
      (3, "mac_rx_packet_count", "int", 0), (4, "mac_crc_error_count", "int", 0),
      (5, "mac_tx_time", "int", 0), (6, "mac_rx_time", "int", 0)],
     []),

    ("C91_G3MACSetup.py", "G3MACSetup", 91, 4, "G3_PLC_MAC_SETUP",
     "G3-PLC MAC Setup - G3-PLC MAC configuration.",
     [(1, "logical_name", "Obis"), (2, "mac_address", "bytes", None),
      (3, "mac_frame_counter", "int", 0), (4, "mac_key", "bytes", None),
      (5, "mac_switch", "bool", False), (6, "mac_security_enabled", "bool", False),
      (7, "mac_security_level", "int", 0), (8, "mac_routing_mode", "int", 0),
      (9, "mac_tx_power", "int", 0), (10, "mac_tx_retries", "int", 0),
      (11, "mac_tx_ack_timeout", "int", 0), (12, "mac_tx_data_rate", "int", 0),
      (13, "mac_tx_power_control", "bool", False)],
     []),

    ("C92_G36LoWPANSetup.py", "G36LoWPANSetup", 92, 4, "G3_PLC_6LOWPAN_ADAPTATION_LAYER_SETUP",
     "G3-PLC 6LoWPAN Adaptation Layer Setup - G3-PLC 6LoWPAN configuration.",
     [(1, "logical_name", "Obis"), (2, "lowpan_enable", "bool", False),
      (3, "lowpan_mtu", "int", 0), (4, "lowpan_fragmentation_timeout", "int", 0),
      (5, "lowpan_fragmentation_retries", "int", 0)],
     []),

    ("C160_G3HybridRFCounters.py", "G3HybridRFCounters", 160, 0, "G3_HYBRID_RF_MAC_LAYER_COUNTERS",
     "G3-PLC Hybrid RF MAC Layer Counters - G3 hybrid RF counters.",
     [(1, "logical_name", "Obis"), (2, "mac_tx_packet_count", "int", 0),
      (3, "mac_rx_packet_count", "int", 0), (4, "mac_crc_error_count", "int", 0),
      (5, "mac_tx_time", "int", 0), (6, "mac_rx_time", "int", 0)],
     []),

    ("C161_G3HybridRFSetup.py", "G3HybridRFSetup", 161, 1, "G3_HYBRID_RF_MAC_SETUP",
     "G3-PLC Hybrid RF MAC Setup - G3 hybrid RF MAC configuration.",
     [(1, "logical_name", "Obis"), (2, "mac_address", "bytes", None),
      (3, "mac_frame_counter", "int", 0), (4, "mac_key", "bytes", None),
      (5, "mac_switch", "bool", False), (6, "mac_security_enabled", "bool", False),
      (7, "mac_security_level", "int", 0), (8, "mac_routing_mode", "int", 0),
      (9, "mac_tx_power", "int", 0), (10, "mac_tx_retries", "int", 0),
      (11, "mac_tx_ack_timeout", "int", 0), (12, "mac_tx_data_rate", "int", 0),
      (13, "mac_tx_power_control", "bool", False)],
     []),

    ("C162_G3Hybrid6LoWPANSetup.py", "G3Hybrid6LoWPANSetup", 162, 1, "G3_HYBRID_6LOWPAN_ADAPTATION_LAYER_SETUP",
     "G3-PLC Hybrid 6LoWPAN Adaptation Layer Setup - G3 hybrid 6LoWPAN configuration.",
     [(1, "logical_name", "Obis"), (2, "lowpan_enable", "bool", False),
      (3, "lowpan_mtu", "int", 0), (4, "lowpan_fragmentation_timeout", "int", 0),
      (5, "lowpan_fragmentation_retries", "int", 0)],
     []),

    # === HS-PLC ===
    ("C140_HSPLCMACSetup.py", "HSPLCMACSetup", 140, 0, "HS_PLC_IEC_12139_1_MAC_SETUP",
     "HS-PLC ISO/IEC 12139-1 MAC Setup - HS-PLC MAC configuration.",
     [(1, "logical_name", "Obis"), (2, "mac_address", "bytes", None),
      (3, "mac_frame_counter", "int", 0), (4, "mac_key", "bytes", None),
      (5, "mac_switch", "bool", False), (6, "mac_security_enabled", "bool", False),
      (7, "mac_security_level", "int", 0)],
     []),

    ("C141_HSPLCCPASSetup.py", "HSPLCCPASSetup", 141, 0, "HS_PLC_IEC_12139_1_CPAS_SETUP",
     "HS-PLC ISO/IEC 12139-1 CPAS Setup - HS-PLC CPAS configuration.",
     [(1, "logical_name", "Obis"), (2, "cpas_enable", "bool", False),
      (3, "cpas_mtu", "int", 0), (4, "cpas_fragmentation_timeout", "int", 0)],
     []),

    ("C142_HSPLCIPSSASSetup.py", "HSPLCIPSSASSetup", 142, 0, "HS_PLC_IEC_12139_1_IP_SSAS_SETUP",
     "HS-PLC ISO/IEC 12139-1 IP SSAS Setup - HS-PLC IP SSAS configuration.",
     [(1, "logical_name", "Obis"), (2, "ip_ssas_enable", "bool", False),
      (3, "ip_ssas_mtu", "int", 0), (4, "ip_ssas_fragmentation_timeout", "int", 0)],
     []),

    ("C143_HSPLCHDLCSSASSetup.py", "HSPLCHDLCSSASSetup", 143, 0, "HS_PLC_IEC_12139_1_HDLC_SSAS_SETUP",
     "HS-PLC ISO/IEC 12139-1 HDLC SSAS Setup - HS-PLC HDLC SSAS configuration.",
     [(1, "logical_name", "Obis"), (2, "hdlc_ssas_enable", "bool", False),
      (3, "hdlc_ssas_mtu", "int", 0), (4, "hdlc_ssas_fragmentation_timeout", "int", 0)],
     []),

    # === ZigBee ===
    ("C101_ZigbeeSASStartup.py", "ZigbeeSASStartup", 101, 0, "ZIGBEE_SAS_STARTUP",
     "ZigBee SAS Startup - ZigBee Smart Energy Profile startup configuration.",
     [(1, "logical_name", "Obis"), (2, "startup_control", "int", 0),
      (3, "channel_mask", "int", 0), (4, "scan_duration", "int", 0),
      (5, "scan_attempts", "int", 0), (6, "scan_attempts_timeout", "int", 0),
      (7, "channel", "int", 0), (8, "security_level", "int", 0),
      (9, "preconfigured_link_key", "bytes", None),
      (10, "network_key", "bytes", None), (11, "network_key_enable", "bool", False),
      (12, "use_insecure_join", "bool", False), (13, "permit_duration", "int", 0),
      (14, "device_timeout", "int", 0)],
     []),

    ("C102_ZigbeeSASJoin.py", "ZigbeeSASJoin", 102, 0, "ZIGBEE_SAS_JOIN",
     "ZigBee SAS Join - ZigBee Smart Energy Profile join configuration.",
     [(1, "logical_name", "Obis"), (2, "join_control", "int", 0),
      (3, "rejoin_interval", "int", 0), (4, "max_rejoin_interval", "int", 0),
      (5, "security_level", "int", 0), (6, "network_key_enable", "bool", False),
      (7, "preconfigured_link_key", "bytes", None),
      (8, "trust_center_address", "bytes", None),
      (9, "trust_center_master_key", "bytes", None),
      (10, "active_network_key_seq_number", "int", 0),
      (11, "link_key", "bytes", None)],
     []),

    ("C103_ZigbeeSASAPSFragmentation.py", "ZigbeeSASAPSFragmentation", 103, 0, "ZIGBEE_SAS_APS_FRAGMENTATION",
     "ZigBee SAS APS Fragmentation - ZigBee APS layer fragmentation setup.",
     [(1, "logical_name", "Obis"), (2, "fragmentation_enabled", "bool", False),
      (3, "window_size", "int", 0), (4, "inter_frame_delay", "int", 0)],
     []),

    ("C104_ZigbeeNetworkControl.py", "ZigbeeNetworkControl", 104, 0, "ZIGBEE_NETWORK_CONTROL",
     "ZigBee Network Control - ZigBee network control and management.",
     [(1, "logical_name", "Obis"), (2, "network_mode", "int", 0),
      (3, "pan_id", "int", 0), (4, "extended_pan_id", "bytes", None),
      (5, "channel", "int", 0), (6, "permit_duration", "int", 0),
      (7, "device_timeout", "int", 0), (8, "router_capacity", "int", 0),
      (9, "end_device_capacity", "int", 0),
      (10, "trust_center_address", "bytes", None),
      (11, "trust_center_master_key", "bytes", None),
      (12, "active_network_key_seq_number", "int", 0),
      (13, "network_key", "bytes", None), (14, "link_key", "bytes", None)],
     []),

    ("C105_ZigbeeTunnelSetup.py", "ZigbeeTunnelSetup", 105, 0, "ZIGBEE_TUNNEL_SETUP",
     "ZigBee Tunnel Setup - ZigBee tunnel configuration.",
     [(1, "logical_name", "Obis"), (2, "tunnel_address", "bytes", None),
      (3, "tunnel_port", "int", 0)],
     []),

    # === LPWAN ===
    ("C126_SCHCLPWANSetup.py", "SCHCLPWANSetup", 126, 0, "SCHC_LPWAN",
     "SCHC LPWAN Setup - SCHC (Static Context Header Compression) LPWAN configuration.",
     [(1, "logical_name", "Obis"), (2, "schc_rule_list", "list", None),
      (3, "schc_parameter_list", "list", None)],
     []),

    ("C127_SCHCLPWANDiagnostic.py", "SCHCLPWANDiagnostic", 127, 0, "SCHC_LPWAN_DIAGNOSTICS",
     "SCHC LPWAN Diagnostic - SCHC LPWAN diagnostics.",
     [(1, "logical_name", "Obis"), (2, "messages_sent", "int", 0),
      (3, "messages_received", "int", 0), (4, "messages_failed", "int", 0),
      (5, "messages_retransmitted", "int", 0)],
     []),

    ("C128_LoRaWANSetup.py", "LoRaWANSetup", 128, 0, "LORAWAN_SETUP",
     "LoRaWAN Setup - LoRaWAN network configuration.",
     [(1, "logical_name", "Obis"), (2, "lorawan_device_eui", "bytes", None),
      (3, "lorawan_app_eui", "bytes", None), (4, "lorawan_app_key", "bytes", None),
      (5, "lorawan_nwk_s_key", "bytes", None), (6, "lorawan_app_s_key", "bytes", None),
      (7, "lorawan_dev_addr", "bytes", None), (8, "lorawan_uplink_counter", "int", 0),
      (9, "lorawan_downlink_counter", "int", 0), (10, "lorawan_adr", "bool", False),
      (11, "lorawan_rx2_data_rate", "int", 0), (12, "lorawan_rx1_delay", "int", 0),
      (13, "lorawan_rx2_frequency", "int", 0)],
     []),

    ("C129_LoRaWANDiagnostic.py", "LoRaWANDiagnostic", 129, 0, "LORAWAN_DIAGNOSTICS",
     "LoRaWAN Diagnostic - LoRaWAN network diagnostics.",
     [(1, "logical_name", "Obis"), (2, "messages_sent", "int", 0),
      (3, "messages_received", "int", 0), (4, "messages_failed", "int", 0),
      (5, "messages_retransmitted", "int", 0), (6, "lorawan_rssi", "int", 0),
      (7, "lorawan_snr", "int", 0)],
     []),

    # === Wi-SUN ===
    ("C95_WiSUNSetup.py", "WiSUNSetup", 95, 0, "WISUN_SETUP",
     "Wi-SUN Setup - Wi-SUN network configuration.",
     [(1, "logical_name", "Obis"), (2, "phy_operating_mode", "int", 0),
      (3, "network_mode", "int", 0), (4, "pan_id", "int", 0),
      (5, "routing_method", "int", 0), (6, "routing_method_parameters", "list", None),
      (7, "phy_operating_mode_list", "list", None),
      (8, "channel_function", "int", 0), (9, "channel_hopping_mode", "int", 0),
      (10, "unicast_dwell_time", "int", 0), (11, "broadcast_dwell_time", "int", 0),
      (12, "broadcast_interval", "int", 0),
      (13, "broadcast_sequence_number", "int", 0),
      (14, "mesh_header_sequence_number", "int", 0),
      (15, "routing_table", "list", None),
      (16, "routing_table_update_time", "bytes", None)],
     []),

    ("C96_WiSUNDiagnostic.py", "WiSUNDiagnostic", 96, 0, "WISUN_DIAGNOSTICS",
     "Wi-SUN Diagnostic - Wi-SUN network diagnostics.",
     [(1, "logical_name", "Obis"), (2, "messages_sent", "int", 0),
      (3, "messages_received", "int", 0), (4, "messages_failed", "int", 0),
      (5, "messages_retransmitted", "int", 0), (6, "phy_tx_total", "int", 0),
      (7, "phy_rx_total", "int", 0), (8, "phy_tx_error", "int", 0),
      (9, "phy_rx_error", "int", 0), (10, "mac_tx_total", "int", 0),
      (11, "mac_rx_total", "int", 0), (12, "mac_tx_error", "int", 0),
      (13, "mac_rx_error", "int", 0)],
     []),

    ("C97_RPLDiagnostic.py", "RPLDiagnostic", 97, 0, "RPL_DIAGNOSTICS",
     "RPL Diagnostic - RPL (Routing Protocol for Low-Power and Lossy Networks) diagnostics.",
     [(1, "logical_name", "Obis"), (2, "parent_address", "bytes", None),
      (3, "parent_rank", "int", 0), (4, "parent_link_metric", "int", 0),
      (5, "parent_link_metric_type", "int", 0),
      (6, "parent_switches", "int", 0),
      (7, "children_addresses", "list", None),
      (8, "children_ranks", "list", None),
      (9, "dao_messages_sent", "int", 0), (10, "dao_messages_received", "int", 0),
      (11, "dio_messages_sent", "int", 0), (12, "dio_messages_received", "int", 0)],
     []),

    ("C98_MPLDiagnostic.py", "MPLDiagnostic", 98, 0, "MPL_DIAGNOSTICS",
     "MPL Diagnostic - MPL (Multicast Protocol for Low-Power and Lossy Networks) diagnostics.",
     [(1, "logical_name", "Obis"), (2, "mpl_domain_id", "bytes", None),
      (3, "mpl_seed_set_version", "int", 0),
      (4, "mpl_trickle_timer_expirations", "int", 0),
      (5, "mpl_messages_sent", "int", 0), (6, "mpl_messages_received", "int", 0),
      (7, "mpl_messages_forwarded", "int", 0)],
     []),

    # === IEC 14908 ===
    ("C130_IEC14908Identification.py", "IEC14908Identification", 130, 0, "IEC_14908_IDENTIFICATION",
     "ISO/IEC 14908 Identification - PLC identification.",
     [(1, "logical_name", "Obis"), (2, "domain_address", "int", 0),
      (3, "subnet_address", "int", 0), (4, "node_address", "int", 0)],
     []),

    ("C131_IEC14908ProtocolSetup.py", "IEC14908ProtocolSetup", 131, 0, "IEC_14908_PROTOCOL_SETUP",
     "ISO/IEC 14908 Protocol Setup - PLC protocol configuration.",
     [(1, "logical_name", "Obis"), (2, "protocol_mode", "int", 0),
      (3, "protocol_version", "int", 0), (4, "protocol_parameters", "list", None)],
     []),

    ("C132_IEC14908ProtocolStatus.py", "IEC14908ProtocolStatus", 132, 0, "IEC_14908_PROTOCOL_STATUS",
     "ISO/IEC 14908 Protocol Status - PLC protocol status.",
     [(1, "logical_name", "Obis"), (2, "protocol_status", "int", 0),
      (3, "connection_status", "int", 0),
      (4, "communication_statistics", "list", None)],
     []),

    ("C133_IEC14908Diagnostic.py", "IEC14908Diagnostic", 133, 0, "IEC_14908_DIAGNOSTICS",
     "ISO/IEC 14908 Diagnostic - PLC diagnostics.",
     [(1, "logical_name", "Obis"), (2, "messages_sent", "int", 0),
      (3, "messages_received", "int", 0), (4, "messages_failed", "int", 0),
      (5, "crc_errors", "int", 0), (6, "timeouts", "int", 0)],
     []),

    # === Token Gateway ===
    ("C115_TokenGateway.py", "TokenGateway", 115, 0, "TOKEN_GATEWAY",
     "Token Gateway - manages token-based operations for payment meters.",
     [(1, "logical_name", "Obis"), (2, "token", "bytes", None),
      (3, "token_time", "bytes", None), (4, "token_status", "int", 0)],
     []),

    # === IEC 62055-41 Attributes ===
    ("C116_IEC62055Attributes.py", "IEC62055Attributes", 116, 0, "IEC_62055_ATTRIBUTES",
     "IEC 62055-41 Attributes - STS (Standard Transfer Specification) key attributes.",
     [(1, "logical_name", "Obis"), (2, "sts_key_identification_no", "int", 0),
      (3, "sts_key_revision_no", "int", 0),
      (4, "sts_key_expiry_date", "bytes", None),
      (5, "sts_token_carrier_identification", "bytes", None),
      (6, "sts_token_decoder_key_status", "int", 0)],
     []),
]


def default_for_type(type_name, default_val):
    """Generate the attr.ib() default."""
    if default_val is not None:
        return f"= {repr(default_val)}"
    if type_name == "Obis":
        return None  # required
    if type_name in ("bytes", "object", "list"):
        return "= None"
    return f"= {repr(default_val)}"


def generate_class(cls_info):
    filename, class_name, class_id, version, enum_name, docstring, attributes, methods = cls_info

    lines = []
    lines.append(f'"""IC class {class_id} - {class_name}.')
    lines.append(f'')
    lines.append(f'{docstring}')
    lines.append(f'')
    lines.append(f'Blue Book: DLMS UA 1000-1 Ed. 16, class_id={class_id}')
    lines.append(f'"""')
    lines.append(f'from typing import Any, ClassVar, Dict, List, Optional')
    lines.append(f'')
    lines.append(f'import attr')
    lines.append(f'')
    lines.append(f'from dlms_cosem import enumerations as enums')
    lines.append(f'from dlms_cosem.cosem.obis import Obis')
    lines.append(f'')
    lines.append(f'')

    # Build attributes string for docstring
    attr_lines = []
    for attr_id, attr_name, *rest in attributes:
        if attr_name == "logical_name":
            attr_lines.append(f'        {attr_id}: logical_name (static)')
        else:
            attr_lines.append(f'        {attr_id}: {attr_name} (dynamic)')

    method_lines = []
    for mid, mname in methods:
        method_lines.append(f'        {mid}: {mname}')

    lines.append(f'@attr.s(auto_attribs=True)')
    lines.append(f'class {class_name}:')
    lines.append(f'    """COSEM IC {class_name} (class_id={class_id}).')
    lines.append(f'')
    if attr_lines:
        lines.append(f'    Attributes:')
        for al in attr_lines:
            lines.append(al)
    if method_lines:
        lines.append(f'    Methods:')
        for ml in method_lines:
            lines.append(ml)
    lines.append(f'    """')
    lines.append(f'')
    lines.append(f'    CLASS_ID: ClassVar[int] = enums.CosemInterface.{enum_name}')
    lines.append(f'    VERSION: ClassVar[int] = {version}')
    lines.append(f'')

    # Attributes
    for attr_id, attr_name, type_name, *rest in attributes:
        default_val = rest[0] if rest else None
        if attr_name == "logical_name":
            lines.append(f'    logical_name: Obis')
        else:
            if default_val is not None:
                lines.append(f'    {attr_name}: Optional[{type_name}] = {repr(default_val)}')
            elif type_name == "list":
                lines.append(f'    {attr_name}: List[Any] = attr.ib(factory=list)')
            elif type_name == "bytes":
                lines.append(f'    {attr_name}: Optional[bytes] = None')
            elif type_name == "bool":
                lines.append(f'    {attr_name}: bool = False')
            elif type_name == "str":
                lines.append(f'    {attr_name}: str = ""')
            elif type_name == "object":
                lines.append(f'    {attr_name}: Optional[Any] = None')
            else:
                lines.append(f'    {attr_name}: int = 0')

    lines.append(f'')
    lines.append(f'    STATIC_ATTRIBUTES: ClassVar[Dict[int, str]] = {{1: "logical_name"}}')
    
    dynamic_attrs = {attr_id: attr_name for attr_id, attr_name, *_ in attributes if attr_name != "logical_name"}
    if dynamic_attrs:
        lines.append(f'    DYNAMIC_ATTRIBUTES: ClassVar[Dict[int, str]] = {repr(dynamic_attrs)}')
    else:
        lines.append(f'    DYNAMIC_ATTRIBUTES: ClassVar[Dict[int, str]] = {{}}')

    if methods:
        lines.append(f'    METHODS: ClassVar[Dict[int, str]] = {repr({mid: mname for mid, mname in methods})}')
    else:
        lines.append(f'    METHODS: ClassVar[Dict[int, str]] = {{}}')

    lines.append(f'')

    # Methods
    for mid, mname in methods:
        lines.append(f'    def {mname}(self) -> None:')
        lines.append(f'        """Method {mid}: {mname}."""')
        lines.append(f'')

    lines.append(f'    def is_static_attribute(self, attribute_id: int) -> bool:')
    lines.append(f'        return attribute_id in self.STATIC_ATTRIBUTES')
    lines.append(f'')

    return "\n".join(lines)


def main():
    for cls_info in CLASSES:
        filename = cls_info[0]
        filepath = os.path.join(BASE_DIR, filename)
        if os.path.exists(filepath):
            print(f"SKIP (exists): {filename}")
            continue
        content = generate_class(cls_info)
        with open(filepath, 'w') as f:
            f.write(content + "\n")
        print(f"CREATED: {filename}")


if __name__ == "__main__":
    main()
