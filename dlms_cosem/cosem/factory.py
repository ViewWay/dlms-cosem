"""COSEM Object Factory - automatic object creation from class_id + logical_name.

Simplifies meter configuration by providing factory methods for all Blue Book
IC classes and pre-configured Chinese GB standard meter setups.
"""
import structlog
from typing import Any, Dict, List, Optional, Type, ClassVar

from dlms_cosem import enumerations as enums
from dlms_cosem.cosem.obis import Obis

LOG = structlog.get_logger()

_registry_cache: Optional[Dict[int, Type]] = None


def _register_classes() -> Dict[int, Type]:
    """Build class_id -> class mapping from all known COSEM classes."""
    from dlms_cosem.cosem.C1_Data import Data
    from dlms_cosem.cosem.C2_Register import Register
    from dlms_cosem.cosem.C3_ExtendedRegister import ExtendedRegister
    from dlms_cosem.cosem.C4_DemandRegister import DemandRegister
    from dlms_cosem.cosem.C205_MaxDemandRegister import MaxDemandRegister
    from dlms_cosem.cosem.C14_RegisterActivation import RegisterActivation
    from dlms_cosem.cosem.C13_RegisterMonitor import RegisterMonitor
    from dlms_cosem.cosem.C61_RegisterTable import RegisterTable
    from dlms_cosem.cosem.value_with_register import ValueWithRegister
    from dlms_cosem.cosem.C6_Clock import Clock
    from dlms_cosem.cosem.C7_ScriptTable import ScriptTable
    from dlms_cosem.cosem.single_action_schedule import SingleActionSchedule
    from dlms_cosem.cosem.C9_ActionSchedule import ActionSchedule
    from dlms_cosem.cosem.C8_SpecialDayTable import SpecialDayTable
    from dlms_cosem.cosem.C5_ProfileGeneric import ProfileGeneric
    from dlms_cosem.cosem.C29_SecuritySetup import SecuritySetup
    from dlms_cosem.cosem.C10_AssociationSN import AssociationSN as AssociationSn
    from dlms_cosem.cosem.C90_LoadProfileSwitch import LoadProfileSwitch
    from dlms_cosem.cosem.event_notification import EventNotification
    from dlms_cosem.cosem.C28_AutoAnswer import AutoAnswer
    from dlms_cosem.cosem.C101_InfraredSetup import InfraredSetup
    from dlms_cosem.cosem.C102_LocalPortSetup import LocalPortSetup
    from dlms_cosem.cosem.C23_RS485Setup import RS485Setup
    from dlms_cosem.cosem.C39_TcpUdpSetup import TcpUdpSetup
    from dlms_cosem.cosem.C24_ModemSetup import ModemSetup
    from dlms_cosem.cosem.C48_ModemConfiguration import ModemConfiguration
    from dlms_cosem.cosem.interrogation_interface import InterrogationInterface
    from dlms_cosem.cosem.attribute_with_selection import CosemAttributeWithSelection
    from dlms_cosem.cosem.gprs_setup import GPRSSetup as GprsSetup
    from dlms_cosem.cosem.C106_NBIoTProfileSetup import NBIoTProfileSetup as NbpSetup
    from dlms_cosem.cosem.C46_ZigBeeSetup import ZigBeeSetup as ZigbeeSetup
    from dlms_cosem.cosem.C35_ImageTransfer import ImageTransferStatus as ImageTransfer
    from dlms_cosem.cosem.quality_control import QualityFlag as QualityControl
    from dlms_cosem.cosem.standard_event_log import StandardEventCode as StandardEventLog
    from dlms_cosem.cosem.utility_event_log import UtilityEventLogEntry as UtilityEventLog
    from dlms_cosem.cosem.C76_EventLog import EventLogEntry as EventLog
    # New IC classes
    from dlms_cosem.cosem.C40_IPv4Setup import IPv4Setup
    from dlms_cosem.cosem.C27_GPRSSetup import GPRSSetup as GprsModemSetup
    from dlms_cosem.cosem.C15_PushSetup import PushSetup
    from dlms_cosem.cosem.C16_DisconnectControl import DisconnectControl
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
    from dlms_cosem.cosem.C45_PPPSetup import PPPSetup
    from dlms_cosem.cosem.C28_SMTPSetup import SMTPSetup
    from dlms_cosem.cosem.C119_ValueTable import ValueTable
    from dlms_cosem.cosem.C32_IecPublicKey import IecPublicKey
    from dlms_cosem.cosem.C83_MbusDiagnostic import MbusDiagnostic
    from dlms_cosem.cosem.C110_PowerQualityMonitor import PowerQualityMonitor
    from dlms_cosem.cosem.C111_HarmonicMonitor import HarmonicMonitor
    from dlms_cosem.cosem.C112_SagSwellMonitor import SagSwellMonitor
    from dlms_cosem.cosem.C62_CompactData import CompactData
    from dlms_cosem.cosem.C55_StatusMapping import StatusMapping
    from dlms_cosem.cosem.C33_CosemDataProtection import CosemDataProtection
    from dlms_cosem.cosem.C78_FunctionControl import FunctionControl
    from dlms_cosem.cosem.C211_ArrayManager import ArrayManager
    from dlms_cosem.cosem.C115_CommPortProtection import CommPortProtection
    from dlms_cosem.cosem.C18_ActivityCalendar import ActivityCalendar
    from dlms_cosem.cosem.C53_SapAssignment import SapAssignment

    return {
        enums.CosemInterface.DATA: Data,
        enums.CosemInterface.REGISTER: Register,
        enums.CosemInterface.EXTENDED_REGISTER: ExtendedRegister,
        enums.CosemInterface.DEMAND_REGISTER: DemandRegister,
        enums.CosemInterface.REGISTER_ACTIVATION: RegisterActivation,
        enums.CosemInterface.REGISTER_MONITOR: RegisterMonitor,
        enums.CosemInterface.REGISTER_TABLE: RegisterTable,
        enums.CosemInterface.CLOCK: Clock,
        enums.CosemInterface.SCRIPT_TABLE: ScriptTable,
        enums.CosemInterface.SINGLE_ACTION_SCHEDULE: SingleActionSchedule,
        enums.CosemInterface.SCHEDULE: ActionSchedule,
        enums.CosemInterface.SPECIAL_DAYS_TABLE: SpecialDayTable,
        enums.CosemInterface.PROFILE_GENERIC: ProfileGeneric,
        enums.CosemInterface.SECURITY_SETUP: SecuritySetup,
        enums.CosemInterface.ASSOCIATION_SN: AssociationSn,
        enums.CosemInterface.AUTO_ANSWER: AutoAnswer,
        enums.CosemInterface.IEC_LOCAL_PORT_SETUP: LocalPortSetup,
        enums.CosemInterface.IEC_HDLC_SETUP: RS485Setup,
        enums.CosemInterface.IEC_TWISTED_PAIR_SETUP: InfraredSetup,
        enums.CosemInterface.MODEM_CONFIGURATION: ModemConfiguration,
        enums.CosemInterface.AUTO_CONNECT: ModemSetup,
        24: ValueWithRegister,
        29: EventNotification,
        106: NbpSetup,
        108: GprsSetup,
        109: TcpUdpSetup,
        110: ZigbeeSetup,
        # New IC classes
        enums.CosemInterface.IPV4_SETUP: IPv4Setup,
        enums.CosemInterface.GPRS_MODEM_SETUP: GprsModemSetup,
        enums.CosemInterface.PUSH: PushSetup,
        enums.CosemInterface.DISCONNECT_CONTROL: DisconnectControl,
        enums.CosemInterface.LIMITER: Limiter,
        enums.CosemInterface.MBUS_CLIENT: MBusClient,
        enums.CosemInterface.PARAMETER_MONITOR: ParameterMonitor,
        enums.CosemInterface.SENSOR_MANAGER: SensorManager,
        enums.CosemInterface.NTP_SETUP: NTPSetup,
        enums.CosemInterface.ACCOUNT: Account,
        enums.CosemInterface.CREDIT: Credit,
        enums.CosemInterface.CHARGE: Charge,
        enums.CosemInterface.ARBITRATOR: Arbitrator,
        enums.CosemInterface.MAC_ADDRESS_SETUP: MACAddressSetup,
        enums.CosemInterface.PPP_SETUP: PPPSetup,
        enums.CosemInterface.SMTP_SETUP: SMTPSetup,
        enums.CosemInterface.VALUE_TABLE: ValueTable,
        enums.CosemInterface.IEC_PUBLIC_KEY: IecPublicKey,
        enums.CosemInterface.MBUS_DIAGNOSTIC: MbusDiagnostic,
        enums.CosemInterface.POWER_QUALITY_MONITOR: PowerQualityMonitor,
        enums.CosemInterface.HARMONIC_MONITOR: HarmonicMonitor,
        enums.CosemInterface.SAG_SWELL_MONITOR: SagSwellMonitor,
        enums.CosemInterface.COMPACT_DATA: CompactData,
        enums.CosemInterface.STATUS_MAPPING: StatusMapping,
        enums.CosemInterface.COSEM_DATA_PROTECTION: CosemDataProtection,
        enums.CosemInterface.FUNCTION_CONTROL: FunctionControl,
        enums.CosemInterface.ARRAY_MANAGER: ArrayManager,
        enums.CosemInterface.COMMUNICATION_PORT_PROTECTION: CommPortProtection,
        enums.CosemInterface.ACTIVITY_CALENDAR: ActivityCalendar,
        enums.CosemInterface.SAP_ASSIGNMENT: SapAssignment,
    }


def _get_registry() -> Dict[int, Type]:
    global _registry_cache
    if _registry_cache is None:
        _registry_cache = _register_classes()
    return _registry_cache


def create_cosem_object(class_id: int, logical_name: Any, **kwargs) -> Any:
    """Create a COSEM object by class_id and logical_name.

    Args:
        class_id: COSEM interface class ID (e.g. 3 for Register)
        logical_name: Obis instance or OBIS byte string (e.g. b'\\x01\\x00...\\xff')
        **kwargs: Additional attributes to set on the created object

    Returns:
        Instantiated COSEM object

    Raises:
        ValueError: If class_id is unknown or logical_name is invalid
    """
    if not isinstance(logical_name, Obis):
        if isinstance(logical_name, (bytes, bytearray)):
            logical_name = Obis.from_bytes(logical_name)
        elif isinstance(logical_name, str):
            logical_name = Obis.from_bytes(bytes.fromhex(logical_name))
        elif isinstance(logical_name, (list, tuple)) and len(logical_name) == 6:
            logical_name = Obis(*logical_name)
        else:
            raise ValueError(f"Cannot convert {type(logical_name)} to Obis")

    registry = _get_registry()
    cls = registry.get(class_id)
    if cls is None:
        LOG.warning("Unknown COSEM class_id", class_id=class_id)
        cls = _generic_object(class_id)

    try:
        obj = cls(logical_name=logical_name, **kwargs)
    except TypeError:
        obj = cls(logical_name=logical_name)
        for k, v in kwargs.items():
            if hasattr(obj, k):
                setattr(obj, k, v)

    return obj


def _generic_object(class_id: int) -> Type:
    """Create a generic COSEM object class for unknown class_ids."""
    import attr

    @attr.s(auto_attribs=True, frozen=False)
    class GenericCosemObject:
        CLASS_ID: ClassVar[int] = class_id
        VERSION: ClassVar[int] = 0
        logical_name: Obis = attr.ib()

        def __attrs_post_init__(self):
            self.value = None

    GenericCosemObject.__name__ = f"GenericCosemObject_{class_id}"
    return GenericCosemObject


def create_china_gb_three_phase_meter() -> Dict[str, Any]:
    """Create a standard Chinese GB three-phase smart meter object model.

    Returns dict mapping obis hex strings -> COSEM object instances.
    """
    from dlms_cosem.cosem.C2_Register import Register
    from dlms_cosem.cosem.C4_DemandRegister import DemandRegister
    from dlms_cosem.cosem.C6_Clock import Clock
    from dlms_cosem.cosem.C5_ProfileGeneric import ProfileGeneric

    objects: Dict[str, Any] = {}

    def _k(a, b, c, d, e, f):
        return Obis(a, b, c, d, e, f).to_bytes().hex()

    # Clock
    objects[_k(0, 0, 1, 0, 0, 255)] = Clock(Obis(0, 0, 1, 0, 0, 255))

    # Import active energy
    for ln, val in [
        ((1, 0, 1, 8, 0, 255), 12345.67),
        ((1, 0, 1, 8, 1, 255), 4115.23),
        ((1, 0, 1, 8, 2, 255), 4089.45),
        ((1, 0, 1, 8, 3, 255), 4140.99),
    ]:
        objects[_k(*ln)] = Register(Obis(*ln), value=val, scaler=-2, unit=30)

    # Export active energy
    for ln, val in [
        ((1, 0, 2, 8, 0, 255), 567.89),
        ((1, 0, 2, 8, 1, 255), 189.63),
        ((1, 0, 2, 8, 2, 255), 187.21),
        ((1, 0, 2, 8, 3, 255), 191.05),
    ]:
        objects[_k(*ln)] = Register(Obis(*ln), value=val, scaler=-2, unit=30)

    # Import reactive energy
    objects[_k(1, 0, 3, 8, 0, 255)] = Register(
        Obis(1, 0, 3, 8, 0, 255), value=2345.67, scaler=-2, unit=31
    )

    # Voltage per phase
    for ln, val in [
        ((1, 0, 32, 7, 0, 255), 220.5),
        ((1, 0, 52, 7, 0, 255), 220.3),
        ((1, 0, 72, 7, 0, 255), 221.1),
    ]:
        objects[_k(*ln)] = Register(Obis(*ln), value=val, scaler=-1, unit=33)

    # Current per phase
    for ln, val in [
        ((1, 0, 31, 7, 0, 255), 5.23),
        ((1, 0, 51, 7, 0, 255), 5.18),
        ((1, 0, 71, 7, 0, 255), 5.31),
    ]:
        objects[_k(*ln)] = Register(Obis(*ln), value=val, scaler=-1, unit=34)

    # Active power
    for ln, val in [
        ((1, 0, 11, 7, 0, 255), 3456.7),
        ((1, 0, 21, 7, 0, 255), 1152.3),
        ((1, 0, 41, 7, 0, 255), 1148.9),
        ((1, 0, 61, 7, 0, 255), 1155.5),
    ]:
        objects[_k(*ln)] = Register(Obis(*ln), value=val, scaler=-1, unit=27)

    # Frequency
    objects[_k(1, 0, 14, 7, 0, 255)] = Register(
        Obis(1, 0, 14, 7, 0, 255), value=50.01, scaler=-2, unit=32
    )

    # Power factor
    objects[_k(1, 0, 13, 7, 0, 255)] = Register(
        Obis(1, 0, 13, 7, 0, 255), value=978, scaler=-3, unit=106
    )

    # Load profile
    objects[_k(1, 0, 99, 1, 0, 255)] = ProfileGeneric(
        Obis(1, 0, 99, 1, 0, 255)
    )

    # Demand register
    objects[_k(1, 0, 12, 7, 0, 255)] = DemandRegister(
        Obis(1, 0, 12, 7, 0, 255)
    )

    return objects


def create_single_phase_meter() -> Dict[str, Any]:
    """Create a standard single-phase smart meter object model."""
    from dlms_cosem.cosem.C2_Register import Register
    from dlms_cosem.cosem.C6_Clock import Clock

    objects: Dict[str, Any] = {}

    def _k(a, b, c, d, e, f):
        return Obis(a, b, c, d, e, f).to_bytes().hex()

    objects[_k(0, 0, 1, 0, 0, 255)] = Clock(Obis(0, 0, 1, 0, 0, 255))
    objects[_k(1, 0, 1, 8, 0, 255)] = Register(
        Obis(1, 0, 1, 8, 0, 255), value=9876.54, scaler=-2, unit=30
    )
    objects[_k(1, 0, 32, 7, 0, 255)] = Register(
        Obis(1, 0, 32, 7, 0, 255), value=220.1, scaler=-1, unit=33
    )
    objects[_k(1, 0, 31, 7, 0, 255)] = Register(
        Obis(1, 0, 31, 7, 0, 255), value=2.56, scaler=-1, unit=34
    )
    objects[_k(1, 0, 11, 7, 0, 255)] = Register(
        Obis(1, 0, 11, 7, 0, 255), value=563.2, scaler=-1, unit=27
    )
    return objects
