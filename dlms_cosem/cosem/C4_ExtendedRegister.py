"""IC004 - Extended Register.

Holds a register value with an associated timestamp (capture_time).
Used for billing period readings, demand resets, etc.

Blue Book: DLMS UA 1000-1 Ed. 14, §4.2.4
"""
from datetime import datetime
from typing import Any, ClassVar, Dict, Optional

import attr

from dlms_cosem import enumerations as enums
from dlms_cosem.cosem.obis import Obis
from dlms_cosem.cosem.C7_ProfileGeneric import AttributeDescription


@attr.s(auto_attribs=True)
class ExtendedRegister:
    """COSEM IC Extended Register (class_id=4).

    Attributes:
        1: logical_name (static)
        2: value (dynamic)
        3: capture_time (dynamic, datetime)
    Methods:
        1: reset
    """

    CLASS_ID: ClassVar[int] = enums.CosemInterface.EXTENDED_REGISTER
    VERSION: ClassVar[int] = 0

    logical_name: Obis
    value: Optional[Any] = None
    capture_time: Optional[datetime] = None
    scaler: int = 0
    unit: int = 0
    status: int = 0

    STATIC_ATTRIBUTES: ClassVar[Dict[int, AttributeDescription]] = {
        1: AttributeDescription(attribute_id=1, attribute_name="logical_name"),
    }
    DYNAMIC_ATTRIBUTES: ClassVar[Dict[int, AttributeDescription]] = {
        2: AttributeDescription(attribute_id=2, attribute_name="value"),
        3: AttributeDescription(attribute_id=3, attribute_name="capture_time"),
    }
    METHODS: ClassVar[Dict[int, str]] = {1: "reset"}

    def reset(self) -> None:
        self.value = 0
        self.capture_time = None

    def is_static_attribute(self, attribute_id: int) -> bool:
        return attribute_id in self.STATIC_ATTRIBUTES
