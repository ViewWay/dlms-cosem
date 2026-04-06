"""IC class 68 - Tariff Plan (Utility Tables).

Defines the tariff plan structure. References season profiles, week profiles,
and day profiles.

Blue Book: DLMS UA 1000-1 Ed. 14
"""
from typing import Any, ClassVar, Dict, List, Optional

import attr

from dlms_cosem import enumerations as enums
from dlms_cosem.cosem.obis import Obis
from dlms_cosem.cosem.C5_ProfileGeneric import AttributeDescription


@attr.s(auto_attribs=True)
class TariffPlan:
    """COSEM IC Tariff Plan (class_id=68, Utility Tables).

    Attributes:
        1: logical_name (static)
        2: energy_price (static)
        3: tariff_entries (static)
    """

    CLASS_ID: ClassVar[int] = enums.CosemInterface.UTILITY_TABLES
    VERSION: ClassVar[int] = 0

    logical_name: Obis
    energy_price: Optional[Any] = None
    tariff_entries: List[Any] = attr.ib(factory=list)

    STATIC_ATTRIBUTES: ClassVar[Dict[int, AttributeDescription]] = {
        1: AttributeDescription(attribute_id=1, attribute_name="logical_name"),
        2: AttributeDescription(attribute_id=2, attribute_name="energy_price"),
        3: AttributeDescription(attribute_id=3, attribute_name="tariff_entries"),
    }
    DYNAMIC_ATTRIBUTES: ClassVar[Dict[int, AttributeDescription]] = {}
    METHODS: ClassVar[Dict[int, str]] = {}

    def is_static_attribute(self, attribute_id: int) -> bool:
        return attribute_id in self.STATIC_ATTRIBUTES
