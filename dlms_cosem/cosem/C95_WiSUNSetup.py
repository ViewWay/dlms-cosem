"""IC class 95 - WiSUNSetup.

Wi-SUN Setup - Wi-SUN network configuration.

Blue Book: DLMS UA 1000-1 Ed. 16, class_id=95
"""
from typing import Any, ClassVar, Dict, List, Optional

import attr

from dlms_cosem import enumerations as enums
from dlms_cosem.cosem.obis import Obis


@attr.s(auto_attribs=True)
class WiSUNSetup:
    """COSEM IC WiSUNSetup (class_id=95).

    Attributes:
        1: logical_name (static)
        2: phy_operating_mode (dynamic)
        3: network_mode (dynamic)
        4: pan_id (dynamic)
        5: routing_method (dynamic)
        6: routing_method_parameters (dynamic)
        7: phy_operating_mode_list (dynamic)
        8: channel_function (dynamic)
        9: channel_hopping_mode (dynamic)
        10: unicast_dwell_time (dynamic)
        11: broadcast_dwell_time (dynamic)
        12: broadcast_interval (dynamic)
        13: broadcast_sequence_number (dynamic)
        14: mesh_header_sequence_number (dynamic)
        15: routing_table (dynamic)
        16: routing_table_update_time (dynamic)
    """

    CLASS_ID: ClassVar[int] = enums.CosemInterface.WISUN_SETUP
    VERSION: ClassVar[int] = 0

    logical_name: Obis
    phy_operating_mode: Optional[int] = 0
    network_mode: Optional[int] = 0
    pan_id: Optional[int] = 0
    routing_method: Optional[int] = 0
    routing_method_parameters: List[Any] = attr.ib(factory=list)
    phy_operating_mode_list: List[Any] = attr.ib(factory=list)
    channel_function: Optional[int] = 0
    channel_hopping_mode: Optional[int] = 0
    unicast_dwell_time: Optional[int] = 0
    broadcast_dwell_time: Optional[int] = 0
    broadcast_interval: Optional[int] = 0
    broadcast_sequence_number: Optional[int] = 0
    mesh_header_sequence_number: Optional[int] = 0
    routing_table: List[Any] = attr.ib(factory=list)
    routing_table_update_time: Optional[bytes] = None

    STATIC_ATTRIBUTES: ClassVar[Dict[int, str]] = {1: "logical_name"}
    DYNAMIC_ATTRIBUTES: ClassVar[Dict[int, str]] = {2: 'phy_operating_mode', 3: 'network_mode', 4: 'pan_id', 5: 'routing_method', 6: 'routing_method_parameters', 7: 'phy_operating_mode_list', 8: 'channel_function', 9: 'channel_hopping_mode', 10: 'unicast_dwell_time', 11: 'broadcast_dwell_time', 12: 'broadcast_interval', 13: 'broadcast_sequence_number', 14: 'mesh_header_sequence_number', 15: 'routing_table', 16: 'routing_table_update_time'}
    METHODS: ClassVar[Dict[int, str]] = {}

    def is_static_attribute(self, attribute_id: int) -> bool:
        return attribute_id in self.STATIC_ATTRIBUTES

