"""IC class 3 - Register.

A Register object holds a single value (scalar) such as an energy reading,
voltage, etc. It is the simplest COSEM interface class for measurement data.

Blue Book: DLMS UA 1000-1 Ed. 14, §4.2.3
"""
from typing import Any, ClassVar, Dict, List, Optional

import attr

from dlms_cosem import enumerations as enums
from dlms_cosem.cosem.obis import Obis
from dlms_cosem.cosem.profile_generic import AttributeDescription


@attr.s(auto_attribs=True)
class Register:
    """COSEM IC Register (class_id=3).

    Attributes:
        1: logical_name (static)
        2: value (dynamic, scaler_unit)
    Methods:
        1: reset
    """

    CLASS_ID: ClassVar[int] = enums.CosemInterface.REGISTER
    VERSION: ClassVar[int] = 0

    logical_name: Obis
    value: Optional[Any] = None
    scaler: int = 0
    unit: int = 0

    STATIC_ATTRIBUTES: ClassVar[Dict[int, AttributeDescription]] = {
        1: AttributeDescription(attribute_id=1, attribute_name="logical_name"),
    }
    DYNAMIC_ATTRIBUTES: ClassVar[Dict[int, AttributeDescription]] = {
        2: AttributeDescription(attribute_id=2, attribute_name="value"),
    }
    METHODS: ClassVar[Dict[int, str]] = {1: "reset"}

    def reset(self) -> None:
        """Method 1: Reset the register value to 0."""
        self.value = 0

    def is_static_attribute(self, attribute_id: int) -> bool:
        return attribute_id in self.STATIC_ATTRIBUTES
