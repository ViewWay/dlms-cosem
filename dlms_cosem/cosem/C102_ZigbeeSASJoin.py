"""IC class 102 - ZigbeeSASJoin.

ZigBee SAS Join - ZigBee Smart Energy Profile join configuration.

Blue Book: DLMS UA 1000-1 Ed. 16, class_id=102
"""
from typing import Any, ClassVar, Dict, List, Optional

import attr

from dlms_cosem import enumerations as enums
from dlms_cosem.cosem.obis import Obis


@attr.s(auto_attribs=True)
class ZigbeeSASJoin:
    """COSEM IC ZigbeeSASJoin (class_id=102).

    Attributes:
        1: logical_name (static)
        2: join_control (dynamic)
        3: rejoin_interval (dynamic)
        4: max_rejoin_interval (dynamic)
        5: security_level (dynamic)
        6: network_key_enable (dynamic)
        7: preconfigured_link_key (dynamic)
        8: trust_center_address (dynamic)
        9: trust_center_master_key (dynamic)
        10: active_network_key_seq_number (dynamic)
        11: link_key (dynamic)
    """

    CLASS_ID: ClassVar[int] = enums.CosemInterface.ZIGBEE_SAS_JOIN
    VERSION: ClassVar[int] = 0

    logical_name: Obis
    join_control: Optional[int] = 0
    rejoin_interval: Optional[int] = 0
    max_rejoin_interval: Optional[int] = 0
    security_level: Optional[int] = 0
    network_key_enable: Optional[bool] = False
    preconfigured_link_key: Optional[bytes] = None
    trust_center_address: Optional[bytes] = None
    trust_center_master_key: Optional[bytes] = None
    active_network_key_seq_number: Optional[int] = 0
    link_key: Optional[bytes] = None

    STATIC_ATTRIBUTES: ClassVar[Dict[int, str]] = {1: "logical_name"}
    DYNAMIC_ATTRIBUTES: ClassVar[Dict[int, str]] = {2: 'join_control', 3: 'rejoin_interval', 4: 'max_rejoin_interval', 5: 'security_level', 6: 'network_key_enable', 7: 'preconfigured_link_key', 8: 'trust_center_address', 9: 'trust_center_master_key', 10: 'active_network_key_seq_number', 11: 'link_key'}
    METHODS: ClassVar[Dict[int, str]] = {}

    def is_static_attribute(self, attribute_id: int) -> bool:
        return attribute_id in self.STATIC_ATTRIBUTES

