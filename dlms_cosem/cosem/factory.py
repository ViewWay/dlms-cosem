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
    from dlms_cosem.cosem.data import Data
    from dlms_cosem.cosem.register import Register
    from dlms_cosem.cosem.extended_register import ExtendedRegister
    from dlms_cosem.cosem.demand_register import DemandRegister
    from dlms_cosem.cosem.max_demand_register import MaxDemandRegister
    from dlms_cosem.cosem.register_activation import RegisterActivation
    from dlms_cosem.cosem.register_monitor import RegisterMonitor
    from dlms_cosem.cosem.register_table import RegisterTable
    from dlms_cosem.cosem.value_with_register import ValueWithRegister
    from dlms_cosem.cosem.clock import Clock
    from dlms_cosem.cosem.script_table import ScriptTable
    from dlms_cosem.cosem.single_action_schedule import SingleActionSchedule
    from dlms_cosem.cosem.action_schedule import ActionSchedule
    from dlms_cosem.cosem.special_day_table import SpecialDayTable
    from dlms_cosem.cosem.profile_generic import ProfileGeneric
    from dlms_cosem.cosem.security_setup import SecuritySetup
    from dlms_cosem.cosem.association_sn import AssociationSN as AssociationSn
    from dlms_cosem.cosem.load_profile_switch import LoadProfileSwitch
    from dlms_cosem.cosem.event_notification import EventNotification
    from dlms_cosem.cosem.auto_answer import AutoAnswer
    from dlms_cosem.cosem.infrared_setup import InfraredSetup
    from dlms_cosem.cosem.lp_setup import LocalPortSetup
    from dlms_cosem.cosem.rs485_setup import RS485Setup
    from dlms_cosem.cosem.tcp_udp_setup import TcpUdpSetup
    from dlms_cosem.cosem.modem_setup import ModemSetup
    from dlms_cosem.cosem.modem_configuration import ModemConfiguration
    from dlms_cosem.cosem.interrogation_interface import InterrogationInterface
    from dlms_cosem.cosem.attribute_with_selection import CosemAttributeWithSelection
    from dlms_cosem.cosem.gprs_setup import GPRSSetup as GprsSetup
    from dlms_cosem.cosem.nbp_setup import NBIoTProfileSetup as NbpSetup
    from dlms_cosem.cosem.zigbee_setup import ZigBeeSetup as ZigbeeSetup
    from dlms_cosem.cosem.image_transfer import ImageTransferStatus as ImageTransfer
    from dlms_cosem.cosem.quality_control import QualityFlag as QualityControl
    from dlms_cosem.cosem.standard_event_log import StandardEventCode as StandardEventLog
    from dlms_cosem.cosem.utility_event_log import UtilityEventLogEntry as UtilityEventLog
    from dlms_cosem.cosem.event_log import EventLogEntry as EventLog

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
    from dlms_cosem.cosem.register import Register
    from dlms_cosem.cosem.demand_register import DemandRegister
    from dlms_cosem.cosem.clock import Clock
    from dlms_cosem.cosem.profile_generic import ProfileGeneric

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
    from dlms_cosem.cosem.register import Register
    from dlms_cosem.cosem.clock import Clock

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
