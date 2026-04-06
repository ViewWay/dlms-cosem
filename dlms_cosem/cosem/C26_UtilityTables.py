"""IC class 26 - UtilityTables.

Utility Tables - stores table cell values for utility data.

Blue Book: DLMS UA 1000-1 Ed. 16, class_id=26
"""
from typing import Any, ClassVar, Dict, List, Optional

import attr

from dlms_cosem import enumerations as enums
from dlms_cosem.cosem.obis import Obis


@attr.s(auto_attribs=True)
class UtilityTables:
    """COSEM IC UtilityTables (class_id=26).

    Attributes:
        1: logical_name (static)
        2: table_cell_values (dynamic)
    """

    CLASS_ID: ClassVar[int] = enums.CosemInterface.UTILITY_TABLES
    VERSION: ClassVar[int] = 0

    logical_name: Obis
    table_cell_values: List[Any] = attr.ib(factory=list)

    STATIC_ATTRIBUTES: ClassVar[Dict[int, str]] = {1: "logical_name"}
    DYNAMIC_ATTRIBUTES: ClassVar[Dict[int, str]] = {2: 'table_cell_values'}
    METHODS: ClassVar[Dict[int, str]] = {}

    def is_static_attribute(self, attribute_id: int) -> bool:
        return attribute_id in self.STATIC_ATTRIBUTES

