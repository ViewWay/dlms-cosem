"""IC class 91 - G3MACSetup.

G3-PLC MAC Setup - G3-PLC MAC configuration.

Blue Book: DLMS UA 1000-1 Ed. 16, class_id=91
"""
from typing import Any, ClassVar, Dict, List, Optional

import attr

from dlms_cosem import enumerations as enums
from dlms_cosem.cosem.obis import Obis


@attr.s(auto_attribs=True)
class G3MACSetup:
    """COSEM IC G3MACSetup (class_id=91).

    Attributes:
        1: logical_name (static)
        2: mac_address (dynamic)
        3: mac_frame_counter (dynamic)
        4: mac_key (dynamic)
        5: mac_switch (dynamic)
        6: mac_security_enabled (dynamic)
        7: mac_security_level (dynamic)
        8: mac_routing_mode (dynamic)
        9: mac_tx_power (dynamic)
        10: mac_tx_retries (dynamic)
        11: mac_tx_ack_timeout (dynamic)
        12: mac_tx_data_rate (dynamic)
        13: mac_tx_power_control (dynamic)
    """

    CLASS_ID: ClassVar[int] = enums.CosemInterface.G3_PLC_MAC_SETUP
    VERSION: ClassVar[int] = 4

    logical_name: Obis
    mac_address: Optional[bytes] = None
    mac_frame_counter: Optional[int] = 0
    mac_key: Optional[bytes] = None
    mac_switch: Optional[bool] = False
    mac_security_enabled: Optional[bool] = False
    mac_security_level: Optional[int] = 0
    mac_routing_mode: Optional[int] = 0
    mac_tx_power: Optional[int] = 0
    mac_tx_retries: Optional[int] = 0
    mac_tx_ack_timeout: Optional[int] = 0
    mac_tx_data_rate: Optional[int] = 0
    mac_tx_power_control: Optional[bool] = False

    STATIC_ATTRIBUTES: ClassVar[Dict[int, str]] = {1: "logical_name"}
    DYNAMIC_ATTRIBUTES: ClassVar[Dict[int, str]] = {2: 'mac_address', 3: 'mac_frame_counter', 4: 'mac_key', 5: 'mac_switch', 6: 'mac_security_enabled', 7: 'mac_security_level', 8: 'mac_routing_mode', 9: 'mac_tx_power', 10: 'mac_tx_retries', 11: 'mac_tx_ack_timeout', 12: 'mac_tx_data_rate', 13: 'mac_tx_power_control'}
    METHODS: ClassVar[Dict[int, str]] = {}

    def is_static_attribute(self, attribute_id: int) -> bool:
        return attribute_id in self.STATIC_ATTRIBUTES

