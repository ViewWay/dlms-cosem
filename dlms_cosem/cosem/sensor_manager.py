"""IC class 67 - Sensor Manager.

Sensor management and monitoring.

Blue Book: DLMS UA 1000-1 Ed. 14, §4.5.10
"""
from typing import Any, ClassVar, Dict, List, Optional

import attr

from dlms_cosem import enumerations as enums
from dlms_cosem.cosem.obis import Obis
from dlms_cosem.cosem.profile_generic import AttributeDescription


@attr.s(auto_attribs=True)
class SensorManager:
    """COSEM IC Sensor Manager (class_id=67).

    Attributes:
        1: logical_name (static)
        2: sensor_list (dynamic) - List of managed sensors
        3: sensor_status (dynamic) - Status of each sensor
        4: totals (dynamic) - Total values from sensors
    Methods:
        1: reset
    """

    CLASS_ID: ClassVar[int] = enums.CosemInterface.SENSOR_MANAGER
    VERSION: ClassVar[int] = 0

    logical_name: Obis
    sensor_list: List[Dict[str, Any]] = attr.ib(factory=list)
    sensor_status: List[int] = attr.ib(factory=list)
    totals: List[Any] = attr.ib(factory=list)

    STATIC_ATTRIBUTES: ClassVar[Dict[int, AttributeDescription]] = {
        1: AttributeDescription(attribute_id=1, attribute_name="logical_name"),
    }
    DYNAMIC_ATTRIBUTES: ClassVar[Dict[int, AttributeDescription]] = {
        2: AttributeDescription(attribute_id=2, attribute_name="sensor_list"),
        3: AttributeDescription(attribute_id=3, attribute_name="sensor_status"),
        4: AttributeDescription(attribute_id=4, attribute_name="totals"),
    }
    METHODS: ClassVar[Dict[int, str]] = {1: "reset"}

    def reset(self) -> None:
        """Method 1: Reset sensor manager."""
        self.sensor_status = []
        self.totals = []

    def is_static_attribute(self, attribute_id: int) -> bool:
        return attribute_id in self.STATIC_ATTRIBUTES

    def add_sensor(self, sensor_obis: Obis, sensor_type: int) -> None:
        """Add a sensor to the manager."""
        self.sensor_list.append({
            "logical_name": sensor_obis,
            "sensor_type": sensor_type,
        })
        self.sensor_status.append(0)  # Initial status
