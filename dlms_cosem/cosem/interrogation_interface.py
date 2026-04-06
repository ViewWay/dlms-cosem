"""IC015 - Interrogation Interface.

Controls meter wakeup and data preparation for remote reading sessions.
Used in NB-IoT and battery-powered meters to manage communication windows.

Blue Book: DLMS UA 1000-1 Ed. 14
"""
from datetime import datetime
from typing import Any, ClassVar, Dict, List, Optional

import attr

from dlms_cosem import enumerations as enums
from dlms_cosem.cosem.obis import Obis
from dlms_cosem.cosem.profile_generic import AttributeDescription


@attr.s(auto_attribs=True)
class InterrogationInterface:
    """COSEM IC Interrogation Interface (class_id=15).

    Controls the meter's response to interrogation requests.

    Attributes:
        1: logical_name (static)
        2: interrogation_level (static, enum)
        3: number_of_objects (static)
        4: interrogation_list (static, list of CosemAttribute)
    Methods:
        1: interrogate
        2: get_interrogation_response
    """

    CLASS_ID: ClassVar[int] = 15
    VERSION: ClassVar[int] = 0

    logical_name: Obis
    interrogation_level: int = 0  # 0=all, 1=static, 2=dynamic
    number_of_objects: int = 0
    interrogation_list: List[Any] = attr.ib(factory=list)

    STATIC_ATTRIBUTES: ClassVar[Dict[int, AttributeDescription]] = {
        1: AttributeDescription(attribute_id=1, attribute_name="logical_name"),
        2: AttributeDescription(attribute_id=2, attribute_name="interrogation_level"),
        3: AttributeDescription(attribute_id=3, attribute_name="number_of_objects"),
        4: AttributeDescription(attribute_id=4, attribute_name="interrogation_list"),
    }
    DYNAMIC_ATTRIBUTES: ClassVar[Dict[int, AttributeDescription]] = {}
    METHODS: ClassVar[Dict[int, str]] = {1: "interrogate", 2: "get_interrogation_response"}

    def interrogate(self, level: Optional[int] = None) -> List[Any]:
        """Method 1: Initiate interrogation at given level."""
        if level is not None:
            self.interrogation_level = level
        return self.interrogation_list

    def is_static_attribute(self, attribute_id: int) -> bool:
        return attribute_id in self.STATIC_ATTRIBUTES
