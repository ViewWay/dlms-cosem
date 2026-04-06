"""IC class 97 - RPLDiagnostic.

RPL Diagnostic - RPL (Routing Protocol for Low-Power and Lossy Networks) diagnostics.

Blue Book: DLMS UA 1000-1 Ed. 16, class_id=97
"""
from typing import Any, ClassVar, Dict, List, Optional

import attr

from dlms_cosem import enumerations as enums
from dlms_cosem.cosem.obis import Obis


@attr.s(auto_attribs=True)
class RPLDiagnostic:
    """COSEM IC RPLDiagnostic (class_id=97).

    Attributes:
        1: logical_name (static)
        2: parent_address (dynamic)
        3: parent_rank (dynamic)
        4: parent_link_metric (dynamic)
        5: parent_link_metric_type (dynamic)
        6: parent_switches (dynamic)
        7: children_addresses (dynamic)
        8: children_ranks (dynamic)
        9: dao_messages_sent (dynamic)
        10: dao_messages_received (dynamic)
        11: dio_messages_sent (dynamic)
        12: dio_messages_received (dynamic)
    """

    CLASS_ID: ClassVar[int] = enums.CosemInterface.RPL_DIAGNOSTICS
    VERSION: ClassVar[int] = 0

    logical_name: Obis
    parent_address: Optional[bytes] = None
    parent_rank: Optional[int] = 0
    parent_link_metric: Optional[int] = 0
    parent_link_metric_type: Optional[int] = 0
    parent_switches: Optional[int] = 0
    children_addresses: List[Any] = attr.ib(factory=list)
    children_ranks: List[Any] = attr.ib(factory=list)
    dao_messages_sent: Optional[int] = 0
    dao_messages_received: Optional[int] = 0
    dio_messages_sent: Optional[int] = 0
    dio_messages_received: Optional[int] = 0

    STATIC_ATTRIBUTES: ClassVar[Dict[int, str]] = {1: "logical_name"}
    DYNAMIC_ATTRIBUTES: ClassVar[Dict[int, str]] = {2: 'parent_address', 3: 'parent_rank', 4: 'parent_link_metric', 5: 'parent_link_metric_type', 6: 'parent_switches', 7: 'children_addresses', 8: 'children_ranks', 9: 'dao_messages_sent', 10: 'dao_messages_received', 11: 'dio_messages_sent', 12: 'dio_messages_received'}
    METHODS: ClassVar[Dict[int, str]] = {}

    def is_static_attribute(self, attribute_id: int) -> bool:
        return attribute_id in self.STATIC_ATTRIBUTES

