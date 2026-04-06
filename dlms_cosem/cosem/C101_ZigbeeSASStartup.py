"""IC class 101 - ZigbeeSASStartup.

ZigBee SAS Startup - ZigBee Smart Energy Profile startup configuration.

Blue Book: DLMS UA 1000-1 Ed. 16, class_id=101
"""
from typing import Any, ClassVar, Dict, List, Optional

import attr

from dlms_cosem import enumerations as enums
from dlms_cosem.cosem.obis import Obis


@attr.s(auto_attribs=True)
class ZigbeeSASStartup:
    """COSEM IC ZigbeeSASStartup (class_id=101).

    Attributes:
        1: logical_name (static)
        2: startup_control (dynamic)
        3: channel_mask (dynamic)
        4: scan_duration (dynamic)
        5: scan_attempts (dynamic)
        6: scan_attempts_timeout (dynamic)
        7: channel (dynamic)
        8: security_level (dynamic)
        9: preconfigured_link_key (dynamic)
        10: network_key (dynamic)
        11: network_key_enable (dynamic)
        12: use_insecure_join (dynamic)
        13: permit_duration (dynamic)
        14: device_timeout (dynamic)
    """

    CLASS_ID: ClassVar[int] = enums.CosemInterface.ZIGBEE_SAS_STARTUP
    VERSION: ClassVar[int] = 0

    logical_name: Obis
    startup_control: Optional[int] = 0
    channel_mask: Optional[int] = 0
    scan_duration: Optional[int] = 0
    scan_attempts: Optional[int] = 0
    scan_attempts_timeout: Optional[int] = 0
    channel: Optional[int] = 0
    security_level: Optional[int] = 0
    preconfigured_link_key: Optional[bytes] = None
    network_key: Optional[bytes] = None
    network_key_enable: Optional[bool] = False
    use_insecure_join: Optional[bool] = False
    permit_duration: Optional[int] = 0
    device_timeout: Optional[int] = 0

    STATIC_ATTRIBUTES: ClassVar[Dict[int, str]] = {1: "logical_name"}
    DYNAMIC_ATTRIBUTES: ClassVar[Dict[int, str]] = {2: 'startup_control', 3: 'channel_mask', 4: 'scan_duration', 5: 'scan_attempts', 6: 'scan_attempts_timeout', 7: 'channel', 8: 'security_level', 9: 'preconfigured_link_key', 10: 'network_key', 11: 'network_key_enable', 12: 'use_insecure_join', 13: 'permit_duration', 14: 'device_timeout'}
    METHODS: ClassVar[Dict[int, str]] = {}

    def is_static_attribute(self, attribute_id: int) -> bool:
        return attribute_id in self.STATIC_ATTRIBUTES

