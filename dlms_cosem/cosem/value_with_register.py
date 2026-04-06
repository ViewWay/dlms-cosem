"""IC024 - Value with Register.

Combines cumulative (register) and instantaneous (value) readings
in a single interface class. Common for energy meters that need
both totalized and real-time values.

Blue Book: DLMS UA 1000-1 Ed. 14
"""
from datetime import datetime
from typing import Any, ClassVar, Dict, Optional

import attr

from dlms_cosem import enumerations as enums
from dlms_cosem.cosem.obis import Obis
from dlms_cosem.cosem.C5_ProfileGeneric import AttributeDescription


@attr.s(auto_attribs=True)
class ValueWithRegister:
    """COSEM IC Value with Register (class_id=24).

    Attributes:
        1: logical_name (static)
        2: value (dynamic, instantaneous reading)
        3: register (dynamic, cumulative reading)
        4: scaler_unit (static)
    Methods:
        1: reset
    """

    CLASS_ID: ClassVar[int] = 24
    VERSION: ClassVar[int] = 0

    logical_name: Obis
    value: Optional[Any] = None
    register: Optional[Any] = None
    scaler: int = 0
    unit: int = 0

    STATIC_ATTRIBUTES: ClassVar[Dict[int, AttributeDescription]] = {
        1: AttributeDescription(attribute_id=1, attribute_name="logical_name"),
        4: AttributeDescription(attribute_id=4, attribute_name="scaler_unit"),
    }
    DYNAMIC_ATTRIBUTES: ClassVar[Dict[int, AttributeDescription]] = {
        2: AttributeDescription(attribute_id=2, attribute_name="value"),
        3: AttributeDescription(attribute_id=3, attribute_name="register"),
    }
    METHODS: ClassVar[Dict[int, str]] = {1: "reset"}

    def reset(self) -> None:
        self.value = 0
        self.register = 0

    def is_static_attribute(self, attribute_id: int) -> bool:
        return attribute_id in self.STATIC_ATTRIBUTES
