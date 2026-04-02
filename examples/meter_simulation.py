"""
Meter Simulation Example - Complete Three-Phase Smart Meter

Simulates a DLMS/COSEM-compliant three-phase electricity meter with:
- Energy registers (import/export, active/reactive per phase)
- Instantaneous power, voltage, current, power factor, frequency
- Load profile (billing + daily)
- Demand register with max tracking
- Clock with tariff support
- Event logging (standard + utility)
- SN association for client connection

Usage:
    python -m examples.meter_simulation

    Or import and use programmatically:
        from examples.meter_simulation import MeterSimulation
        meter = MeterSimulation()
        meter.connect_client("localhost", 4059)
"""
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple

from dlms_cosem.cosem.obis import Obis
from dlms_cosem.cosem import (
    Register, ExtendedRegister, DemandRegister, MaxDemandRegister,
    ValueWithRegister, ProfileGeneric, ProfileType, BufferOverflow,
    Clock, StandardEventLog, StandardEventCode,
    UtilityEventLog, EventNotification, QualityControl, QualityFlag,
    InterrogationInterface, LoadProfileSwitch,
    SecuritySetup, AssociationSN,
    GPRSSetup, TcpUdpSetup, ZigBeeSetup,
    create_energy_register, create_power_register,
    create_voltage_register, create_current_register,
    create_pf_register, create_frequency_register,
)


class MeterSimulation:
    """Simulates a complete three-phase DLMS smart meter.

    The meter exposes all standard COSEM objects and supports
    attribute read/write and method invocation via SN association.
    """

    MANUFACTURER = "SIMU"
    FIRMWARE_VERSION = "1.0.0"
    SERIAL_NUMBER = "SIM12345678"

    def __init__(self, meter_address: str = "SIM12345678"):
        self.meter_address = meter_address
        self.connected = False
        self.sn_association: Optional[AssociationSN] = None

        # COSEM object map: (class_id, obis_tuple) -> instance
        self.objects: Dict[Tuple[int, Tuple[int, ...]], Any] = {}

        self._init_energy_registers()
        self._init_power_registers()
        self._init_voltage_current()
        self._init_profiles()
        self._init_demand()
        self._init_clock()
        self._init_events()
        self._init_comms()
        self._init_misc()

    def _register(self, obj: Any) -> None:
        """Register a COSEM object by (class_id, obis_tuple)."""
        ln = obj.logical_name
        key = (getattr(obj, 'CLASS_ID', 0), (ln.a, ln.b, ln.c, ln.d, ln.e, ln.f))
        self.objects[key] = obj

    def _get_obis(self, a=0, b=0, c=0, d=0, e=0, f=255) -> Obis:
        return Obis(a=a, b=b, c=c, d=d, e=e, f=f)

    def _init_energy_registers(self):
        # Active import total
        self.active_import = create_energy_register("1.0.0.0.0.255")
        self._register(self.active_import)
        # Active export total
        self.active_export = create_energy_register("2.0.0.0.0.255")
        self._register(self.active_export)
        # Reactive import/export
        self.reactive_import = create_energy_register("3.0.0.0.0.255")
        self._register(self.reactive_import)
        self.reactive_export = create_energy_register("4.0.0.0.0.255")
        self._register(self.reactive_export)
        # Per-phase active import
        for phase, c in [(1, 1), (2, 2), (3, 3)]:
            reg = create_energy_register(f"1.{c}.0.0.0.255")
            self._register(reg)

    def _init_power_registers(self):
        self.power_total = create_power_register("0.0.0.0.0.255")
        self._register(self.power_total)
        for phase, c in [(1, 1), (2, 2), (3, 3)]:
            reg = create_power_register(f"0.{c}.0.0.0.255")
            self._register(reg)

    def _init_voltage_current(self):
        self.voltage_L1 = create_voltage_register("0.0.1.0.0.255")
        self.voltage_L2 = create_voltage_register("0.0.2.0.0.255")
        self.voltage_L3 = create_voltage_register("0.0.3.0.0.255")
        self._register(self.voltage_L1)
        self._register(self.voltage_L2)
        self._register(self.voltage_L3)

        self.current_L1 = create_current_register("0.0.11.0.0.255")
        self.current_L2 = create_current_register("0.0.12.0.0.255")
        self.current_L3 = create_current_register("0.0.13.0.0.255")
        self._register(self.current_L1)
        self._register(self.current_L2)
        self._register(self.current_L3)

        self.power_factor = create_pf_register("0.0.23.0.0.255")
        self._register(self.power_factor)
        self.frequency = create_frequency_register("0.0.14.0.0.255")
        self._register(self.frequency)

    def _init_profiles(self):
        # Billing load profile
        self.billing_profile = ProfileGeneric(
            logical_name=self._get_obis(1, 0, 99, 1, 0, 255),
            capture_period=900,  # 15 min
            profile_entries=4032,  # 42 days
            profile_type=ProfileType.BILLING,
            overflow_strategy=BufferOverflow.OVERWRITE_OLDEST,
        )
        self._register(self.billing_profile)

        # Daily load profile
        self.daily_profile = ProfileGeneric(
            logical_name=self._get_obis(1, 0, 99, 2, 0, 255),
            capture_period=60,  # 1 min
            profile_entries=1440,  # 1 day
            profile_type=ProfileType.DAILY,
            overflow_strategy=BufferOverflow.OVERWRITE_OLDEST,
        )
        self._register(self.daily_profile)

        # Load profile switch
        self.profile_switch = LoadProfileSwitch(
            logical_name=self._get_obis(0, 0, 13, 0, 0, 255),
        )
        self.profile_switch.add_profile("billing", "1.0.99.1.0.255")
        self.profile_switch.add_profile("daily", "1.0.99.2.0.255")
        self._register(self.profile_switch)

    def _init_demand(self):
        self.demand_register = MaxDemandRegister(
            logical_name=self._get_obis(1, 0, 12, 7, 0, 255),
            period=900,
        )
        self._register(self.demand_register)

    def _init_clock(self):
        self.clock = Clock(
            logical_name=self._get_obis(0, 0, 1, 0, 0, 255),
        )
        self._register(self.clock)

    def _init_events(self):
        self.standard_events = StandardEventLog(
            logical_name=self._get_obis(0, 0, 96, 11, 0, 255),
        )
        self._register(self.standard_events)

        self.utility_events = UtilityEventLog(
            logical_name=self._get_obis(0, 0, 96, 12, 0, 255),
        )
        self.utility_events.register_event_code(101, "Phase A voltage sag")
        self.utility_events.register_event_code(102, "Phase B voltage sag")
        self.utility_events.register_event_code(103, "Phase C voltage sag")
        self.utility_events.register_event_code(201, "Transformer tap change")
        self._register(self.utility_events)

        self.event_notification = EventNotification(
            logical_name=self._get_obis(0, 0, 96, 13, 0, 255),
        )
        self._register(self.event_notification)

    def _init_comms(self):
        self.gprs_setup = GPRSSetup(
            logical_name=self._get_obis(0, 0, 40, 0, 0, 255),
            apn="metering.apn",
        )
        self._register(self.gprs_setup)

        self.tcp_setup = TcpUdpSetup(
            logical_name=self._get_obis(0, 0, 41, 0, 0, 255),
            remote_ip="10.0.0.1",
            remote_port=4059,
        )
        self._register(self.tcp_setup)

        self.zigbee_setup = ZigBeeSetup(
            logical_name=self._get_obis(0, 0, 42, 0, 0, 255),
        )
        self._register(self.zigbee_setup)

    def _init_misc(self):
        self.quality_control = QualityControl(
            logical_name=self._get_obis(0, 0, 96, 14, 0, 255),
        )
        self._register(self.quality_control)

        self.interrogation = InterrogationInterface(
            logical_name=self._get_obis(0, 0, 14, 0, 0, 255),
        )
        self._register(self.interrogation)

        self.security_setup = SecuritySetup(
            logical_name=self._get_obis(0, 0, 43, 0, 0, 255),
        )
        self._register(self.security_setup)

    # --- SN Association ---

    def setup_sn_association(self, system_title: bytes, client_sap: int = 16) -> AssociationSN:
        """Setup SN association for client connection."""
        self.sn_association = AssociationSN(
            logical_name=self._get_obis(0, 0, 40, 0, 0, 0),
            server_system_title=system_title,
        )
        self.connected = True
        return self.sn_association

    # --- Read/Write Interface ---

    def get_object(self, class_id: int, obis: Tuple[int, ...]) -> Optional[Any]:
        """Get a COSEM object by class_id and OBIS."""
        return self.objects.get((class_id, obis))

    def read_attribute(self, class_id: int, obis: Tuple[int, ...],
                       attribute_id: int) -> Any:
        """Read an attribute from a COSEM object."""
        obj = self.get_object(class_id, obis)
        if obj is None:
            raise ValueError(f"Object not found: class={class_id}, obis={obis}")

        # Attribute 1 is always logical_name
        if attribute_id == 1:
            return obj.logical_name

        # Map attribute_id to possible instance attribute names
        _attr_names = {
            2: ["value", "buffer", "current_value", "last_average_value", "entries", "status", "enabled", "notification_count"],
            3: ["capture_time", "last_average_value", "capture_objects", "last_max_value", "last_max_time", "quality_description", "current_profile"],
            4: ["capture_period", "status", "sort_object", "quality_timestamp", "switch_time"],
            5: ["sort_method", "switch_active"],
            6: ["sort_object", "profile_list"],
            7: ["entries_in_use"],
            8: ["profile_entries"],
        }

        if attribute_id in _attr_names:
            for name in _attr_names[attribute_id]:
                if hasattr(obj, name):
                    return getattr(obj, name)

        return None

    def write_attribute(self, class_id: int, obis: Tuple[int, ...],
                        attribute_id: int, value: Any) -> None:
        """Write an attribute to a COSEM object."""
        obj = self.get_object(class_id, obis)
        if obj is None:
            raise ValueError(f"Object not found: class={class_id}, obis={obis}")
        if attribute_id == 2:
            if hasattr(obj, 'value'):
                obj.value = value
            elif hasattr(obj, 'buffer'):
                obj.buffer = value
            elif hasattr(obj, 'current_value'):
                obj.current_value = value

    # --- Simulation ---

    def simulate_reading(self, voltage: float = 220.0, current: float = 5.0,
                         power_factor: float = 0.95) -> None:
        """Simulate a single meter reading capture."""
        import math
        power = voltage * current * power_factor
        energy_increment = power / 3600.0  # Wh per second

        # Update energy registers
        for obj in self.objects.values():
            if isinstance(obj, Register) and obj.logical_name.c == 0 and obj.logical_name.b == 0:
                if obj.value is not None:
                    obj.value += energy_increment

        # Update power
        self.power_total.value = power

        # Update voltage/current
        self.voltage_L1.value = voltage
        self.voltage_L2.value = voltage
        self.voltage_L3.value = voltage
        self.current_L1.value = current
        self.current_L2.value = current
        self.current_L3.value = current
        self.power_factor.value = power_factor
        self.frequency.value = 50.0

        # Update demand
        self.demand_register.update_demand(power)

        # Capture to profiles
        self.billing_profile.capture([power])
        self.daily_profile.capture([voltage, current, power])

    def simulate_events(self) -> None:
        """Simulate some meter events."""
        self.standard_events.add_event(StandardEventCode.POWER_RESTORED)
        self.standard_events.add_event(StandardEventCode.TARIFF_CHANGED, event_data="T1->T2")
        self.utility_events.add_event(101, event_data={"voltage": 198.5, "duration": 3.2})

    def get_all_readings(self) -> Dict[str, Any]:
        """Get all meter readings as a dict."""
        return {
            "active_import": self.active_import.value,
            "active_export": self.active_export.value,
            "voltage_L1": self.voltage_L1.value,
            "voltage_L2": self.voltage_L2.value,
            "voltage_L3": self.voltage_L3.value,
            "current_L1": self.current_L1.value,
            "current_L2": self.current_L2.value,
            "current_L3": self.current_L3.value,
            "power_total": self.power_total.value,
            "power_factor": self.power_factor.value,
            "frequency": self.frequency.value,
            "max_demand": self.demand_register.last_max_value,
            "billing_entries": self.billing_profile.entries_in_use,
            "standard_events": len(self.standard_events.entries),
            "utility_events": len(self.utility_events.entries),
        }


if __name__ == "__main__":
    meter = MeterSimulation()

    # Setup SN association
    meter.setup_sn_association(system_title=b"\x01\x02\x03\x04\x05\x06\x07\x08")

    # Simulate some readings
    for _ in range(10):
        meter.simulate_reading()

    # Simulate events
    meter.simulate_events()

    # Print readings
    print("=== Meter Simulation Results ===")
    readings = meter.get_all_readings()
    for k, v in readings.items():
        print(f"  {k}: {v}")

    print(f"\nTotal COSEM objects: {len(meter.objects)}")
    print(f"Connected: {meter.connected}")
