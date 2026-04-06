"""IC class 103 - ZigbeeSASAPSFragmentation.

ZigBee SAS APS Fragmentation - ZigBee APS layer fragmentation setup.

Blue Book: DLMS UA 1000-1 Ed. 16, class_id=103
"""
from typing import Any, ClassVar, Dict, List, Optional

import attr

from dlms_cosem import enumerations as enums
from dlms_cosem.cosem.obis import Obis


@attr.s(auto_attribs=True)
class ZigbeeSASAPSFragmentation:
    """COSEM IC ZigbeeSASAPSFragmentation (class_id=103).

    Attributes:
        1: logical_name (static)
        2: fragmentation_enabled (dynamic)
        3: window_size (dynamic)
        4: inter_frame_delay (dynamic)
    """

    CLASS_ID: ClassVar[int] = enums.CosemInterface.ZIGBEE_SAS_APS_FRAGMENTATION
    VERSION: ClassVar[int] = 0

    logical_name: Obis
    fragmentation_enabled: Optional[bool] = False
    window_size: Optional[int] = 0
    inter_frame_delay: Optional[int] = 0

    STATIC_ATTRIBUTES: ClassVar[Dict[int, str]] = {1: "logical_name"}
    DYNAMIC_ATTRIBUTES: ClassVar[Dict[int, str]] = {2: 'fragmentation_enabled', 3: 'window_size', 4: 'inter_frame_delay'}
    METHODS: ClassVar[Dict[int, str]] = {}

    def is_static_attribute(self, attribute_id: int) -> bool:
        return attribute_id in self.STATIC_ATTRIBUTES

