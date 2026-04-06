"""IC class 56 - SFSKReportingSystemList.

S-FSK Reporting System List - list of S-FSK reporting systems.

Blue Book: DLMS UA 1000-1 Ed. 16, class_id=56
"""
from typing import Any, ClassVar, Dict, List, Optional

import attr

from dlms_cosem import enumerations as enums
from dlms_cosem.cosem.obis import Obis


@attr.s(auto_attribs=True)
class SFSKReportingSystemList:
    """COSEM IC SFSKReportingSystemList (class_id=56).

    Attributes:
        1: logical_name (static)
        2: reporting_system_list (dynamic)
    """

    CLASS_ID: ClassVar[int] = enums.CosemInterface.S_FSK_REPORTING_SYSTEM_LIST
    VERSION: ClassVar[int] = 0

    logical_name: Obis
    reporting_system_list: List[Any] = attr.ib(factory=list)

    STATIC_ATTRIBUTES: ClassVar[Dict[int, str]] = {1: "logical_name"}
    DYNAMIC_ATTRIBUTES: ClassVar[Dict[int, str]] = {2: 'reporting_system_list'}
    METHODS: ClassVar[Dict[int, str]] = {}

    def is_static_attribute(self, attribute_id: int) -> bool:
        return attribute_id in self.STATIC_ATTRIBUTES

