"""IC class 130 - IEC14908Identification.

ISO/IEC 14908 Identification - PLC identification.

Blue Book: DLMS UA 1000-1 Ed. 16, class_id=130
"""
from typing import Any, ClassVar, Dict, List, Optional

import attr

from dlms_cosem import enumerations as enums
from dlms_cosem.cosem.obis import Obis


@attr.s(auto_attribs=True)
class IEC14908Identification:
    """COSEM IC IEC14908Identification (class_id=130).

    Attributes:
        1: logical_name (static)
        2: domain_address (dynamic)
        3: subnet_address (dynamic)
        4: node_address (dynamic)
    """

    CLASS_ID: ClassVar[int] = enums.CosemInterface.IEC_14908_IDENTIFICATION
    VERSION: ClassVar[int] = 0

    logical_name: Obis
    domain_address: Optional[int] = 0
    subnet_address: Optional[int] = 0
    node_address: Optional[int] = 0

    STATIC_ATTRIBUTES: ClassVar[Dict[int, str]] = {1: "logical_name"}
    DYNAMIC_ATTRIBUTES: ClassVar[Dict[int, str]] = {2: 'domain_address', 3: 'subnet_address', 4: 'node_address'}
    METHODS: ClassVar[Dict[int, str]] = {}

    def is_static_attribute(self, attribute_id: int) -> bool:
        return attribute_id in self.STATIC_ATTRIBUTES

