"""IC class 72 - M-Bus Client.

M-Bus client for reading M-Bus slave devices.

Blue Book: DLMS UA 1000-1 Ed. 14, §4.4.5
"""
from typing import Any, ClassVar, Dict, List, Optional

import attr

from dlms_cosem import enumerations as enums
from dlms_cosem.cosem.obis import Obis
from dlms_cosem.cosem.C5_ProfileGeneric import AttributeDescription


@attr.s(auto_attribs=True)
class MBusClient:
    """COSEM IC M-Bus Client (class_id=72).

    Attributes:
        1: logical_name (static)
        2: mbus_port_reference (dynamic) - Reference to M-Bus port
        3: capture_definition (dynamic) - What data to capture
        4: capture_period (dynamic) - Period between captures
        5: primary_addresses (dynamic) - List of primary addresses
        6: identification_number (dynamic) - M-Bus identification number
        7: manufacturer_id (dynamic) - Manufacturer identifier
        8: version (dynamic) - M-Bus device version
        9: device_type (dynamic) - Type of M-Bus device
        10: access_number (dynamic) - Access counter
        11: status (dynamic) - M-Bus status
        12: alarm (dynamic) - M-Bus alarm status
    Methods:
        1: reset
        2: capture
    """

    CLASS_ID: ClassVar[int] = enums.CosemInterface.MBUS_CLIENT
    VERSION: ClassVar[int] = 0

    logical_name: Obis
    mbus_port_reference: Optional[Obis] = None
    capture_definition: List[Dict[str, Any]] = attr.ib(factory=list)
    capture_period: int = 0
    primary_addresses: List[int] = attr.ib(factory=list)
    identification_number: str = ""
    manufacturer_id: str = ""
    version: int = 0
    device_type: int = 0
    access_number: int = 0
    status: int = 0
    alarm: int = 0

    STATIC_ATTRIBUTES: ClassVar[Dict[int, AttributeDescription]] = {
        1: AttributeDescription(attribute_id=1, attribute_name="logical_name"),
    }
    DYNAMIC_ATTRIBUTES: ClassVar[Dict[int, AttributeDescription]] = {
        2: AttributeDescription(attribute_id=2, attribute_name="mbus_port_reference"),
        3: AttributeDescription(attribute_id=3, attribute_name="capture_definition"),
        4: AttributeDescription(attribute_id=4, attribute_name="capture_period"),
        5: AttributeDescription(attribute_id=5, attribute_name="primary_addresses"),
        6: AttributeDescription(attribute_id=6, attribute_name="identification_number"),
        7: AttributeDescription(attribute_id=7, attribute_name="manufacturer_id"),
        8: AttributeDescription(attribute_id=8, attribute_name="version"),
        9: AttributeDescription(attribute_id=9, attribute_name="device_type"),
        10: AttributeDescription(attribute_id=10, attribute_name="access_number"),
        11: AttributeDescription(attribute_id=11, attribute_name="status"),
        12: AttributeDescription(attribute_id=12, attribute_name="alarm"),
    }
    METHODS: ClassVar[Dict[int, str]] = {
        1: "reset",
        2: "capture",
    }

    def reset(self) -> None:
        """Method 1: Reset M-Bus client to defaults."""
        self.capture_definition = []
        self.capture_period = 0
        self.access_number = 0
        self.status = 0
        self.alarm = 0

    def capture(self) -> None:
        """Method 2: Trigger immediate data capture."""
        self.access_number += 1

    def is_static_attribute(self, attribute_id: int) -> bool:
        return attribute_id in self.STATIC_ATTRIBUTES
