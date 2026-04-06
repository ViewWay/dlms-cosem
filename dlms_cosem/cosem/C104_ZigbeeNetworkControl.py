"""IC class 104 - ZigbeeNetworkControl.

ZigBee Network Control - ZigBee network control and management.

Blue Book: DLMS UA 1000-1 Ed. 16, class_id=104
"""
from typing import Any, ClassVar, Dict, List, Optional

import attr

from dlms_cosem import enumerations as enums
from dlms_cosem.cosem.obis import Obis


@attr.s(auto_attribs=True)
class ZigbeeNetworkControl:
    """COSEM IC ZigbeeNetworkControl (class_id=104).

    Attributes:
        1: logical_name (static)
        2: network_mode (dynamic)
        3: pan_id (dynamic)
        4: extended_pan_id (dynamic)
        5: channel (dynamic)
        6: permit_duration (dynamic)
        7: device_timeout (dynamic)
        8: router_capacity (dynamic)
        9: end_device_capacity (dynamic)
        10: trust_center_address (dynamic)
        11: trust_center_master_key (dynamic)
        12: active_network_key_seq_number (dynamic)
        13: network_key (dynamic)
        14: link_key (dynamic)
    """

    CLASS_ID: ClassVar[int] = enums.CosemInterface.ZIGBEE_NETWORK_CONTROL
    VERSION: ClassVar[int] = 0

    logical_name: Obis
    network_mode: Optional[int] = 0
    pan_id: Optional[int] = 0
    extended_pan_id: Optional[bytes] = None
    channel: Optional[int] = 0
    permit_duration: Optional[int] = 0
    device_timeout: Optional[int] = 0
    router_capacity: Optional[int] = 0
    end_device_capacity: Optional[int] = 0
    trust_center_address: Optional[bytes] = None
    trust_center_master_key: Optional[bytes] = None
    active_network_key_seq_number: Optional[int] = 0
    network_key: Optional[bytes] = None
    link_key: Optional[bytes] = None

    STATIC_ATTRIBUTES: ClassVar[Dict[int, str]] = {1: "logical_name"}
    DYNAMIC_ATTRIBUTES: ClassVar[Dict[int, str]] = {2: 'network_mode', 3: 'pan_id', 4: 'extended_pan_id', 5: 'channel', 6: 'permit_duration', 7: 'device_timeout', 8: 'router_capacity', 9: 'end_device_capacity', 10: 'trust_center_address', 11: 'trust_center_master_key', 12: 'active_network_key_seq_number', 13: 'network_key', 14: 'link_key'}
    METHODS: ClassVar[Dict[int, str]] = {}

    def is_static_attribute(self, attribute_id: int) -> bool:
        return attribute_id in self.STATIC_ATTRIBUTES

