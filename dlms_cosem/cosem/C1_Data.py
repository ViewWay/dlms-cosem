"""IC class 1 - Data.

Generic data container. Holds a single arbitrary DLMS data value.

Blue Book: DLMS UA 1000-1 Ed. 14, §4.2.1
"""
from typing import Any, ClassVar, Dict, Optional

import attr

from dlms_cosem import enumerations as enums
from dlms_cosem.cosem.obis import Obis
from dlms_cosem.cosem.C7_ProfileGeneric import AttributeDescription


@attr.s(auto_attribs=True)
class Data:
    """COSEM IC Data (class_id=1).

    Attributes:
        1: logical_name (static)
        2: value (dynamic)
    Methods:
        1: reset
    """

    CLASS_ID: ClassVar[int] = enums.CosemInterface.DATA
    VERSION: ClassVar[int] = 0

    logical_name: Obis
    value: Optional[Any] = None

    STATIC_ATTRIBUTES: ClassVar[Dict[int, AttributeDescription]] = {
        1: AttributeDescription(attribute_id=1, attribute_name="logical_name"),
    }
    DYNAMIC_ATTRIBUTES: ClassVar[Dict[int, AttributeDescription]] = {
        2: AttributeDescription(attribute_id=2, attribute_name="value"),
    }
    METHODS: ClassVar[Dict[int, str]] = {1: "reset"}

    def reset(self) -> None:
        self.value = None

    def is_static_attribute(self, attribute_id: int) -> bool:
        return attribute_id in self.STATIC_ATTRIBUTES
