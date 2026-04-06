"""IC class 61 - Register Table.

Holds a table of register values. Used for displaying multiple related
registers (e.g., multi-tariff energy registers).

Blue Book: DLMS UA 1000-1 Ed. 14
"""
from typing import Any, ClassVar, Dict, List, Optional

import attr

from dlms_cosem import enumerations as enums
from dlms_cosem.cosem.obis import Obis
from dlms_cosem.cosem.C5_ProfileGeneric import AttributeDescription


@attr.s(auto_attribs=True)
class RegisterTable:
    """COSEM IC Register Table (class_id=61).

    Attributes:
        1: logical_name (static)
        2: values (dynamic) - table of values (long-unsigned)
    Methods:
        1: reset
    """

    CLASS_ID: ClassVar[int] = enums.CosemInterface.REGISTER_TABLE
    VERSION: ClassVar[int] = 0

    logical_name: Obis
    values: List[List[Any]] = attr.ib(factory=list)

    STATIC_ATTRIBUTES: ClassVar[Dict[int, AttributeDescription]] = {
        1: AttributeDescription(attribute_id=1, attribute_name="logical_name"),
    }
    DYNAMIC_ATTRIBUTES: ClassVar[Dict[int, AttributeDescription]] = {
        2: AttributeDescription(attribute_id=2, attribute_name="values"),
    }
    METHODS: ClassVar[Dict[int, str]] = {1: "reset"}

    def reset(self) -> None:
        self.values = []

    def is_static_attribute(self, attribute_id: int) -> bool:
        return attribute_id in self.STATIC_ATTRIBUTES
