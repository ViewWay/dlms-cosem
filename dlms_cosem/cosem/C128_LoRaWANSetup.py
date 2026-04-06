"""IC class 128 - LoRaWANSetup.

LoRaWAN Setup - LoRaWAN network configuration.

Blue Book: DLMS UA 1000-1 Ed. 16, class_id=128
"""
from typing import Any, ClassVar, Dict, List, Optional

import attr

from dlms_cosem import enumerations as enums
from dlms_cosem.cosem.obis import Obis


@attr.s(auto_attribs=True)
class LoRaWANSetup:
    """COSEM IC LoRaWANSetup (class_id=128).

    Attributes:
        1: logical_name (static)
        2: lorawan_device_eui (dynamic)
        3: lorawan_app_eui (dynamic)
        4: lorawan_app_key (dynamic)
        5: lorawan_nwk_s_key (dynamic)
        6: lorawan_app_s_key (dynamic)
        7: lorawan_dev_addr (dynamic)
        8: lorawan_uplink_counter (dynamic)
        9: lorawan_downlink_counter (dynamic)
        10: lorawan_adr (dynamic)
        11: lorawan_rx2_data_rate (dynamic)
        12: lorawan_rx1_delay (dynamic)
        13: lorawan_rx2_frequency (dynamic)
    """

    CLASS_ID: ClassVar[int] = enums.CosemInterface.LORAWAN_SETUP
    VERSION: ClassVar[int] = 0

    logical_name: Obis
    lorawan_device_eui: Optional[bytes] = None
    lorawan_app_eui: Optional[bytes] = None
    lorawan_app_key: Optional[bytes] = None
    lorawan_nwk_s_key: Optional[bytes] = None
    lorawan_app_s_key: Optional[bytes] = None
    lorawan_dev_addr: Optional[bytes] = None
    lorawan_uplink_counter: Optional[int] = 0
    lorawan_downlink_counter: Optional[int] = 0
    lorawan_adr: Optional[bool] = False
    lorawan_rx2_data_rate: Optional[int] = 0
    lorawan_rx1_delay: Optional[int] = 0
    lorawan_rx2_frequency: Optional[int] = 0

    STATIC_ATTRIBUTES: ClassVar[Dict[int, str]] = {1: "logical_name"}
    DYNAMIC_ATTRIBUTES: ClassVar[Dict[int, str]] = {2: 'lorawan_device_eui', 3: 'lorawan_app_eui', 4: 'lorawan_app_key', 5: 'lorawan_nwk_s_key', 6: 'lorawan_app_s_key', 7: 'lorawan_dev_addr', 8: 'lorawan_uplink_counter', 9: 'lorawan_downlink_counter', 10: 'lorawan_adr', 11: 'lorawan_rx2_data_rate', 12: 'lorawan_rx1_delay', 13: 'lorawan_rx2_frequency'}
    METHODS: ClassVar[Dict[int, str]] = {}

    def is_static_attribute(self, attribute_id: int) -> bool:
        return attribute_id in self.STATIC_ATTRIBUTES

