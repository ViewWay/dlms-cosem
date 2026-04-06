#!/usr/bin/env python3
"""Rename IC class files to C{n}_{ClassName}.py format and update all imports."""
import os
import re
import sys

COSEM_DIR = 'dlms_cosem/cosem'

# Mapping: old_filename -> (class_id, main_class_name)
# For files with CLASS_ID, use the correct CosemInterface value
# For files without CLASS_ID but known to be IC classes, manually assign
RENAME_MAP = {
    # Core IC classes with CLASS_ID
    'data.py': (1, 'Data'),
    'register.py': (2, 'Register'),
    'extended_register.py': (3, 'ExtendedRegister'),
    'demand_register.py': (4, 'DemandRegister'),
    'profile_generic.py': (5, 'ProfileGeneric'),
    'clock.py': (6, 'Clock'),
    'script_table.py': (7, 'ScriptTable'),
    'special_day_table.py': (8, 'SpecialDayTable'),
    'action_schedule.py': (9, 'ActionSchedule'),
    'association_sn.py': (10, 'AssociationSN'),
    'register_monitor.py': (13, 'RegisterMonitor'),
    'register_activation.py': (14, 'RegisterActivation'),
    'push_setup.py': (15, 'PushSetup'),
    'disconnect_control.py': (16, 'DisconnectControl'),
    'limiter.py': (17, 'Limiter'),
    'activity_calendar.py': (18, 'ActivityCalendar'),
    'day_profile.py': (19, 'DayProfile'),  # UTILITY_TABLES but it's DayProfile helper
    'week_profile.py': (20, 'WeekProfile'),
    'sap_assignment.py': (53, 'SapAssignment'),
    'status_mapping.py': (55, 'StatusMapping'),
    'sensor_manager.py': (57, 'SensorManager'),
    'compact_data.py': (62, 'CompactData'),
    'security_setup.py': (29, 'SecuritySetup'),
    'credit.py': (66, 'Credit'),
    'charge.py': (67, 'Charge'),
    'arbitrator.py': (82, 'Arbitrator'),
    'mbus_diagnostic.py': (83, 'MbusDiagnostic'),
    'ntp_setup.py': (87, 'NTPSetup'),
    'load_profile_switch.py': (90, 'LoadProfileSwitch'),
    'lp_setup.py': (100, 'LocalPortSetup'),
    'rs485_setup.py': (23, 'RS485Setup'),  # IEC_HDLC_SETUP=23
    'infrared_setup.py': (102, 'InfraredSetup'),
    'ipv4_setup.py': (40, 'IPv4Setup'),
    'ppp_setup.py': (45, 'PPPSetup'),
    'gprs_modem_setup.py': (27, 'GPRSSetup'),  # GPRS_MODEM_SETUP=27
    'modem_setup.py': (24, 'ModemSetup'),  # MODEM_CONFIGURATION=24
    'modem_configuration.py': (48, 'ModemConfiguration'),  # AUTO_CONNECT=48
    'mbus_client.py': (26, 'MBusClient'),
    'parameter_monitor.py': (79, 'ParameterMonitor'),
    'power_quality_monitor.py': (110, 'PowerQualityMonitor'),
    'harmonic_monitor.py': (111, 'HarmonicMonitor'),
    'sag_swell_monitor.py': (112, 'SagSwellMonitor'),
    'comm_port_protection.py': (115, 'CommPortProtection'),
    'mac_address_setup.py': (117, 'MACAddressSetup'),
    'value_table.py': (119, 'ValueTable'),
    'iec_public_key.py': (32, 'IecPublicKey'),
    'cosem_data_protection.py': (33, 'CosemDataProtection'),
    'function_control.py': (78, 'FunctionControl'),
    'array_manager.py': (211, 'ArrayManager'),
    'smtp_setup.py': (28, 'SMTPSetup'),
    'max_demand_register.py': (205, 'MaxDemandRegister'),  # MAXIMUM_DEMAND
    'event_log.py': (76, 'EventLog'),  # EVENT_LOG=76 (was wrongly PROFILE_GENERIC)
    'account.py': (22, 'Account'),
    'auto_answer.py': (48, 'AutoAnswer'),  # AUTO_ANSWER - wait, AUTO_ANSWER doesn't exist in enum

    # Helper types / support files - keep as is:
    # association.py, attribute_with_selection.py, capture_object.py,
    # current.py, energy_register.py, frequency.py, power_factor.py,
    # power_register.py, voltage.py, interrogation_interface.py,
    # tariff_plan.py, tariff_table.py, season_profile.py (helper for ActivityCalendar)
}

# Files without CLASS_ID that are known IC classes - need to check CosemInterface
NO_CLASS_ID_IC = {
    'load_profile_switch.py': 90,  # LOAD_PROFILE_SWITCH
    'gprs_setup.py': None,  # ? 
    'nbp_setup.py': 106,  # NBIOT_SETUP
    'lora_setup.py': 107,  # LORAWAN_SETUP
    'tcp_udp_setup.py': 39,  # TCP_UDP_SETUP
    'zigbee_setup.py': 46,  # ZIGBEE_SETUP
    'event_notification.py': None,  # ?
    'image_transfer.py': 35,  # IMAGE_TRANSFER
    'standard_event_log.py': 76,  # EVENT_LOG
    'utility_event_log.py': 77,  # EVENT_LOGGER
    'quality_control.py': None,  # ?
    'value_with_register.py': None,  # ?
}

print("Checking AUTO_ANSWER in CosemInterface...")
from dlms_cosem.enumerations import CosemInterface
print(f"  AUTO_ANSWER = {CosemInterface.AUTO_ANSWER.value if hasattr(CosemInterface, 'AUTO_ANSWER') else 'NOT FOUND'}")

# Check which enum names exist
for name in ['AUTO_ANSWER', 'GPRS_SETUP', 'EVENT_NOTIFICATION', 'QUALITY_CONTROL', 'MAXIMUM_DEMAND']:
    if hasattr(CosemInterface, name):
        print(f"  {name} = {CosemInterface[name].value}")
    else:
        print(f"  {name} = NOT FOUND")
