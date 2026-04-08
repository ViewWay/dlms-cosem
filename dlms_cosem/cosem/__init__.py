"""COSEM Interface Classes - Lazy-loaded for reduced memory footprint.

This module uses __getattr__ for lazy loading to reduce initial import time
and memory usage. Only the most commonly used classes are imported immediately.
"""
from __future__ import annotations

# Immediately import only the most commonly used classes
from dlms_cosem.cosem.attribute_with_selection import CosemAttributeWithSelection
from dlms_cosem.cosem.base import CosemAttribute, CosemMethod
from dlms_cosem.cosem.obis import Obis

__all__ = [
    # Core classes (immediately available)
    "CosemAttribute", "CosemMethod", "Obis", "CosemAttributeWithSelection",
    # Blue Book COSEM Interface Classes (lazy loaded)
    "Data", "Register", "ExtendedRegister", "MaxDemandRegister",
    "ValueWithRegister", "RegisterMonitor", "RegisterActivation",
    "DemandRegister", "RegisterTable", "SingleActionSchedule", "ActionSchedule",
    "ScriptTable", "ProfileGeneric", "SortMethod", "ProfileType", "BufferOverflow",
    "Clock", "SpecialDayTable",
    # Tariff and scheduling
    "TariffPlan", "TariffTable", "SeasonProfile", "WeekProfile", "DayProfile",
    # Communication setup
    "LocalPortSetup", "RS485Setup", "InfraredSetup", "ModemSetup",
    "AutoAnswer", "ModemConfiguration", "NBIoTProfileSetup", "LoRaWANSetup",
    # Event logging
    "EventLog", "StandardEventLog", "StandardEventCode",
    "UtilityEventLog", "EventNotification",
    # Quality and monitoring
    "QualityControl", "QualityFlag",
    "InterrogationInterface", "LoadProfileSwitch",
    # Security and association
    "SecuritySetup", "AssociationSN",
    # Network setup
    "GPRSSetup", "TcpUdpSetup", "ZigBeeSetup",
    # Factory helpers
    "create_energy_register", "create_power_register",
    "create_voltage_register", "create_current_register",
    "create_pf_register", "create_frequency_register",
    # OBIS constants
    "OBIS_ACTIVE_IMPORT", "OBIS_ACTIVE_EXPORT",
    "OBIS_REACTIVE_IMPORT", "OBIS_REACTIVE_EXPORT",
    # Additional classes
    "ValueTable", "ValueEntry", "ValueDescriptor",
    "IecPublicKey", "KeyAlgorithm", "KeyUsage",
    "MbusDiagnostic", "PowerQualityMonitor", "HarmonicMonitor", "MonitoringMode",
    "SagSwellMonitor", "CompactData", "CompactDataField",
    "StatusMapping", "StatusMappingEntry",
    "CosemDataProtection", "ProtectedObject",
    "FunctionControl", "FunctionControlEntry",
    "ArrayManager", "CommPortProtection", "ProtectedPort",
    "ActivityCalendar", "ActivityPeriod",
    "SapAssignment", "SapAssignmentEntry",
    # Blue Book Ed.16
    "UtilityTables", "MeasurementDataMonitoring", "AutoConnect",
    "GSMDiagnostic", "LTEMonitoring",
    "MBusSlavePortSetup", "WirelessModeQChannel", "MBusMasterPortSetup", "DLMSMBusPortSetup",
    "IPv6Setup", "CoAPSetup", "CoAPDiagnostic",
    "SFSKPhyMACSetup", "SFSKActiveInitiator", "SFSKMACSyncTimeouts", "SFSKMACCounters",
    "IEC61334LLCSetup", "SFSKReportingSystemList",
    "LLCType1Setup", "LLCType2Setup", "LLCType3Setup",
    "PRIMELLCSSCSSetup", "PRIMEPhysicalCounters", "PRIMEMACSetup", "PRIMEMACFuncParams",
    "PRIMEMACCounters", "PRIMEMACNetworkAdmin", "PRIMEAppIdentification",
    "G3MACCounters", "G3MACSetup", "G36LoWPANSetup",
    "G3HybridRFCounters", "G3HybridRFSetup", "G3Hybrid6LoWPANSetup",
    "HSPLCMACSetup", "HSPLCCPASSetup", "HSPLCIPSSASSetup", "HSPLCHDLCSSASSetup",
    "ZigbeeSASStartup", "ZigbeeSASJoin", "ZigbeeSASAPSFragmentation",
    "ZigbeeNetworkControl", "ZigbeeTunnelSetup",
    "SCHCLPWANSetup", "SCHCLPWANDiagnostic", "LoRaWANSetup", "LoRaWANDiagnostic",
    "WiSUNSetup", "WiSUNDiagnostic", "RPLDiagnostic", "MPLDiagnostic",
    "IEC14908Identification", "IEC14908ProtocolSetup", "IEC14908ProtocolStatus", "IEC14908Diagnostic",
    "TokenGateway", "IEC62055Attributes",
]


def __getattr__(name: str):
    """Lazy import COSEM classes on first access.

    This function is called when an attribute is not found in the module.
    It dynamically imports the requested class and caches it for future use.
    """
    import importlib

    # Mapping of lazy-loaded class names to their (module_path, attr_name) tuples
    _lazy_modules: dict[str, tuple[str, str]] = {
        # Core classes
        "Data": ("dlms_cosem.cosem.C1_Data", "Data"),
        "Register": ("dlms_cosem.cosem.C3_Register", "Register"),
        "ExtendedRegister": ("dlms_cosem.cosem.C4_ExtendedRegister", "ExtendedRegister"),
        "MaxDemandRegister": ("dlms_cosem.cosem.max_demand_register", "MaxDemandRegister"),
        "ValueWithRegister": ("dlms_cosem.cosem.value_with_register", "ValueWithRegister"),
        "RegisterMonitor": ("dlms_cosem.cosem.C21_RegisterMonitor", "RegisterMonitor"),
        "RegisterActivation": ("dlms_cosem.cosem.C6_RegisterActivation", "RegisterActivation"),
        "DemandRegister": ("dlms_cosem.cosem.C5_DemandRegister", "DemandRegister"),
        "RegisterTable": ("dlms_cosem.cosem.C61_RegisterTable", "RegisterTable"),
        "SingleActionSchedule": ("dlms_cosem.cosem.C22_SingleActionSchedule", "SingleActionSchedule"),
        "ActionSchedule": ("dlms_cosem.cosem.C10_Schedule", "ActionSchedule"),
        "ScriptTable": ("dlms_cosem.cosem.C9_ScriptTable", "ScriptTable"),
        "ProfileGeneric": ("dlms_cosem.cosem.C7_ProfileGeneric", "ProfileGeneric"),
        "SortMethod": ("dlms_cosem.cosem.C7_ProfileGeneric", "SortMethod"),
        "ProfileType": ("dlms_cosem.cosem.C7_ProfileGeneric", "ProfileType"),
        "BufferOverflow": ("dlms_cosem.cosem.C7_ProfileGeneric", "BufferOverflow"),
        "Clock": ("dlms_cosem.cosem.C8_Clock", "Clock"),
        "SpecialDayTable": ("dlms_cosem.cosem.C11_SpecialDaysTable", "SpecialDayTable"),
        "TariffPlan": ("dlms_cosem.cosem.tariff_plan", "TariffPlan"),
        "TariffTable": ("dlms_cosem.cosem.tariff_table", "TariffTable"),
        "SeasonProfile": ("dlms_cosem.cosem.season_profile", "SeasonProfile"),
        "WeekProfile": ("dlms_cosem.cosem.week_profile", "WeekProfile"),
        "DayProfile": ("dlms_cosem.cosem.day_profile", "DayProfile"),
        "LocalPortSetup": ("dlms_cosem.cosem.C19_IECLocalPortSetup", "LocalPortSetup"),
        "RS485Setup": ("dlms_cosem.cosem.C23_IECHDLCSetup", "RS485Setup"),
        "InfraredSetup": ("dlms_cosem.cosem.C24_IECTwistedPairSetup", "InfraredSetup"),
        "ModemSetup": ("dlms_cosem.cosem.modem_setup", "ModemSetup"),
        "AutoAnswer": ("dlms_cosem.cosem.C28_AutoAnswer", "AutoAnswer"),
        "ModemConfiguration": ("dlms_cosem.cosem.C27_ModemConfiguration", "ModemConfiguration"),
        "NBIoTProfileSetup": ("dlms_cosem.cosem.nbp_setup", "NBIoTProfileSetup"),
        "EventLog": ("dlms_cosem.cosem.event_log", "EventLog"),
        "StandardEventLog": ("dlms_cosem.cosem.standard_event_log", "StandardEventLog"),
        "StandardEventCode": ("dlms_cosem.cosem.standard_event_log", "StandardEventCode"),
        "UtilityEventLog": ("dlms_cosem.cosem.utility_event_log", "UtilityEventLog"),
        "EventNotification": ("dlms_cosem.cosem.event_notification", "EventNotification"),
        "QualityControl": ("dlms_cosem.cosem.quality_control", "QualityControl"),
        "QualityFlag": ("dlms_cosem.cosem.quality_control", "QualityFlag"),
        "InterrogationInterface": ("dlms_cosem.cosem.interrogation_interface", "InterrogationInterface"),
        "LoadProfileSwitch": ("dlms_cosem.cosem.load_profile_switch", "LoadProfileSwitch"),
        "SecuritySetup": ("dlms_cosem.cosem.C64_SecuritySetup", "SecuritySetup"),
        "AssociationSN": ("dlms_cosem.cosem.C12_AssociationSN", "AssociationSN"),
        "GPRSSetup": ("dlms_cosem.cosem.gprs_setup", "GPRSSetup"),
        "TcpUdpSetup": ("dlms_cosem.cosem.C41_TCPUDPSetup", "TcpUdpSetup"),
        "ZigBeeSetup": ("dlms_cosem.cosem.zigbee_setup", "ZigBeeSetup"),
        "create_energy_register": ("dlms_cosem.cosem.energy_register", "create_energy_register"),
        "create_power_register": ("dlms_cosem.cosem.power_register", "create_power_register"),
        "create_voltage_register": ("dlms_cosem.cosem.voltage", "create_voltage_register"),
        "create_current_register": ("dlms_cosem.cosem.current", "create_current_register"),
        "create_pf_register": ("dlms_cosem.cosem.power_factor", "create_pf_register"),
        "create_frequency_register": ("dlms_cosem.cosem.frequency", "create_frequency_register"),
        "OBIS_ACTIVE_IMPORT": ("dlms_cosem.cosem.energy_register", "OBIS_ACTIVE_IMPORT"),
        "OBIS_ACTIVE_EXPORT": ("dlms_cosem.cosem.energy_register", "OBIS_ACTIVE_EXPORT"),
        "OBIS_REACTIVE_IMPORT": ("dlms_cosem.cosem.energy_register", "OBIS_REACTIVE_IMPORT"),
        "OBIS_REACTIVE_EXPORT": ("dlms_cosem.cosem.energy_register", "OBIS_REACTIVE_EXPORT"),
        "ValueTable": ("dlms_cosem.cosem.value_table", "ValueTable"),
        "ValueEntry": ("dlms_cosem.cosem.value_table", "ValueEntry"),
        "ValueDescriptor": ("dlms_cosem.cosem.value_table", "ValueDescriptor"),
        "IecPublicKey": ("dlms_cosem.cosem.iec_public_key", "IecPublicKey"),
        "KeyAlgorithm": ("dlms_cosem.cosem.iec_public_key", "KeyAlgorithm"),
        "KeyUsage": ("dlms_cosem.cosem.iec_public_key", "KeyUsage"),
        "MbusDiagnostic": ("dlms_cosem.cosem.C77_MBusDiagnostic", "MbusDiagnostic"),
        "PowerQualityMonitor": ("dlms_cosem.cosem.power_quality_monitor", "PowerQualityMonitor"),
        "HarmonicMonitor": ("dlms_cosem.cosem.harmonic_monitor", "HarmonicMonitor"),
        "MonitoringMode": ("dlms_cosem.cosem.harmonic_monitor", "MonitoringMode"),
        "SagSwellMonitor": ("dlms_cosem.cosem.sag_swell_monitor", "SagSwellMonitor"),
        "CompactData": ("dlms_cosem.cosem.C62_CompactData", "CompactData"),
        "CompactDataField": ("dlms_cosem.cosem.C62_CompactData", "CompactDataField"),
        "StatusMapping": ("dlms_cosem.cosem.C63_StatusMapping", "StatusMapping"),
        "StatusMappingEntry": ("dlms_cosem.cosem.C63_StatusMapping", "StatusMappingEntry"),
        "CosemDataProtection": ("dlms_cosem.cosem.C30_COSEMDataProtection", "CosemDataProtection"),
        "ProtectedObject": ("dlms_cosem.cosem.C30_COSEMDataProtection", "ProtectedObject"),
        "FunctionControl": ("dlms_cosem.cosem.C122_FunctionControl", "FunctionControl"),
        "FunctionControlEntry": ("dlms_cosem.cosem.C122_FunctionControl", "FunctionControlEntry"),
        "ArrayManager": ("dlms_cosem.cosem.C123_ArrayManager", "ArrayManager"),
        "CommPortProtection": ("dlms_cosem.cosem.C124_CommPortProtection", "CommPortProtection"),
        "ProtectedPort": ("dlms_cosem.cosem.C124_CommPortProtection", "ProtectedPort"),
        "ActivityCalendar": ("dlms_cosem.cosem.C20_ActivityCalendar", "ActivityCalendar"),
        "ActivityPeriod": ("dlms_cosem.cosem.C20_ActivityCalendar", "ActivityPeriod"),
        "SapAssignment": ("dlms_cosem.cosem.C17_SAPAssignment", "SapAssignment"),
        "SapAssignmentEntry": ("dlms_cosem.cosem.C17_SAPAssignment", "SapAssignmentEntry"),
        # Blue Book Ed.16 classes (lazy loaded)
        "UtilityTables": ("dlms_cosem.cosem.C26_UtilityTables", "UtilityTables"),
        "MeasurementDataMonitoring": ("dlms_cosem.cosem.C66_MeasurementDataMonitoring", "MeasurementDataMonitoring"),
        "AutoConnect": ("dlms_cosem.cosem.C29_AutoConnect", "AutoConnect"),
        "GSMDiagnostic": ("dlms_cosem.cosem.C47_GSMDiagnostic", "GSMDiagnostic"),
        "LTEMonitoring": ("dlms_cosem.cosem.C151_LTEMonitoring", "LTEMonitoring"),
        "MBusSlavePortSetup": ("dlms_cosem.cosem.C25_MBusSlavePortSetup", "MBusSlavePortSetup"),
        "WirelessModeQChannel": ("dlms_cosem.cosem.C73_WirelessModeQChannel", "WirelessModeQChannel"),
        "MBusMasterPortSetup": ("dlms_cosem.cosem.C74_MBusMasterPortSetup", "MBusMasterPortSetup"),
        "DLMSMBusPortSetup": ("dlms_cosem.cosem.C76_DLMSMBusPortSetup", "DLMSMBusPortSetup"),
        "IPv6Setup": ("dlms_cosem.cosem.C48_IPv6Setup", "IPv6Setup"),
        "CoAPSetup": ("dlms_cosem.cosem.C152_CoAPSetup", "CoAPSetup"),
        "CoAPDiagnostic": ("dlms_cosem.cosem.C153_CoAPDiagnostic", "CoAPDiagnostic"),
        "SFSKPhyMACSetup": ("dlms_cosem.cosem.C50_SFSKPhyMACSetup", "SFSKPhyMACSetup"),
        "SFSKActiveInitiator": ("dlms_cosem.cosem.C51_SFSKActiveInitiator", "SFSKActiveInitiator"),
        "SFSKMACSyncTimeouts": ("dlms_cosem.cosem.C52_SFSKMACSyncTimeouts", "SFSKMACSyncTimeouts"),
        "SFSKMACCounters": ("dlms_cosem.cosem.C53_SFSKMACCounters", "SFSKMACCounters"),
        "IEC61334LLCSetup": ("dlms_cosem.cosem.C55_IEC61334LLCSetup", "IEC61334LLCSetup"),
        "SFSKReportingSystemList": ("dlms_cosem.cosem.C56_SFSKReportingSystemList", "SFSKReportingSystemList"),
        "LLCType1Setup": ("dlms_cosem.cosem.C57_LLCType1Setup", "LLCType1Setup"),
        "LLCType2Setup": ("dlms_cosem.cosem.C58_LLCType2Setup", "LLCType2Setup"),
        "LLCType3Setup": ("dlms_cosem.cosem.C59_LLCType3Setup", "LLCType3Setup"),
        "PRIMELLCSSCSSetup": ("dlms_cosem.cosem.C80_PRIMELLCSSCSSetup", "PRIMELLCSSCSSetup"),
        "PRIMEPhysicalCounters": ("dlms_cosem.cosem.C81_PRIMEPhysicalCounters", "PRIMEPhysicalCounters"),
        "PRIMEMACSetup": ("dlms_cosem.cosem.C82_PRIMEMACSetup", "PRIMEMACSetup"),
        "PRIMEMACFuncParams": ("dlms_cosem.cosem.C83_PRIMEMACFuncParams", "PRIMEMACFuncParams"),
        "PRIMEMACCounters": ("dlms_cosem.cosem.C84_PRIMEMACCounters", "PRIMEMACCounters"),
        "PRIMEMACNetworkAdmin": ("dlms_cosem.cosem.C85_PRIMEMACNetworkAdmin", "PRIMEMACNetworkAdmin"),
        "PRIMEAppIdentification": ("dlms_cosem.cosem.C86_PRIMEAppIdentification", "PRIMEAppIdentification"),
        "G3MACCounters": ("dlms_cosem.cosem.C90_G3MACCounters", "G3MACCounters"),
        "G3MACSetup": ("dlms_cosem.cosem.C91_G3MACSetup", "G3MACSetup"),
        "G36LoWPANSetup": ("dlms_cosem.cosem.C92_G36LoWPANSetup", "G36LoWPANSetup"),
        "G3HybridRFCounters": ("dlms_cosem.cosem.C160_G3HybridRFCounters", "G3HybridRFCounters"),
        "G3HybridRFSetup": ("dlms_cosem.cosem.C161_G3HybridRFSetup", "G3HybridRFSetup"),
        "G3Hybrid6LoWPANSetup": ("dlms_cosem.cosem.C162_G3Hybrid6LoWPANSetup", "G3Hybrid6LoWPANSetup"),
        "HSPLCMACSetup": ("dlms_cosem.cosem.C140_HSPLCMACSetup", "HSPLCMACSetup"),
        "HSPLCCPASSetup": ("dlms_cosem.cosem.C141_HSPLCCPASSetup", "HSPLCCPASSetup"),
        "HSPLCIPSSASSetup": ("dlms_cosem.cosem.C142_HSPLCIPSSASSetup", "HSPLCIPSSASSetup"),
        "HSPLCHDLCSSASSetup": ("dlms_cosem.cosem.C143_HSPLCHDLCSSASSetup", "HSPLCHDLCSSASSetup"),
        "ZigbeeSASStartup": ("dlms_cosem.cosem.C101_ZigbeeSASStartup", "ZigbeeSASStartup"),
        "ZigbeeSASJoin": ("dlms_cosem.cosem.C102_ZigbeeSASJoin", "ZigbeeSASJoin"),
        "ZigbeeSASAPSFragmentation": ("dlms_cosem.cosem.C103_ZigbeeSASAPSFragmentation", "ZigbeeSASAPSFragmentation"),
        "ZigbeeNetworkControl": ("dlms_cosem.cosem.C104_ZigbeeNetworkControl", "ZigbeeNetworkControl"),
        "ZigbeeTunnelSetup": ("dlms_cosem.cosem.C105_ZigbeeTunnelSetup", "ZigbeeTunnelSetup"),
        "SCHCLPWANSetup": ("dlms_cosem.cosem.C126_SCHCLPWANSetup", "SCHCLPWANSetup"),
        "SCHCLPWANDiagnostic": ("dlms_cosem.cosem.C127_SCHCLPWANDiagnostic", "SCHCLPWANDiagnostic"),
        "LoRaWANSetup": ("dlms_cosem.cosem.C128_LoRaWANSetup", "LoRaWANSetup"),
        "LoRaWANDiagnostic": ("dlms_cosem.cosem.C129_LoRaWANDiagnostic", "LoRaWANDiagnostic"),
        "WiSUNSetup": ("dlms_cosem.cosem.C95_WiSUNSetup", "WiSUNSetup"),
        "WiSUNDiagnostic": ("dlms_cosem.cosem.C96_WiSUNDiagnostic", "WiSUNDiagnostic"),
        "RPLDiagnostic": ("dlms_cosem.cosem.C97_RPLDiagnostic", "RPLDiagnostic"),
        "MPLDiagnostic": ("dlms_cosem.cosem.C98_MPLDiagnostic", "MPLDiagnostic"),
        "IEC14908Identification": ("dlms_cosem.cosem.C130_IEC14908Identification", "IEC14908Identification"),
        "IEC14908ProtocolSetup": ("dlms_cosem.cosem.C131_IEC14908ProtocolSetup", "IEC14908ProtocolSetup"),
        "IEC14908ProtocolStatus": ("dlms_cosem.cosem.C132_IEC14908ProtocolStatus", "IEC14908ProtocolStatus"),
        "IEC14908Diagnostic": ("dlms_cosem.cosem.C133_IEC14908Diagnostic", "IEC14908Diagnostic"),
        "TokenGateway": ("dlms_cosem.cosem.C115_TokenGateway", "TokenGateway"),
        "IEC62055Attributes": ("dlms_cosem.cosem.C116_IEC62055Attributes", "IEC62055Attributes"),
    }

    if name in _lazy_modules:
        module_path, attr_name = _lazy_modules[name]
        module = importlib.import_module(module_path)
        value = getattr(module, attr_name)
        # Cache the imported value in globals() for faster subsequent access
        globals()[name] = value
        return value

    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
