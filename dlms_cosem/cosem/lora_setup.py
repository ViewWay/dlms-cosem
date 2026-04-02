"""IC class 107 - LoRaWAN Setup.

Configuration for LoRaWAN communication.
Blue Book addition for LPWAN smart metering.

Supports:
- Class A/B/C device modes
- LoRaWAN 1.0.x / 1.1 adaptation
- CN470 frequency band (China)
- Data fragmentation for payload limits
- ADR (Adaptive Data Rate)
"""
from enum import IntEnum
from typing import Any, ClassVar, Dict, Optional

import attr

from dlms_cosem import enumerations as enums
from dlms_cosem.cosem.obis import Obis
from dlms_cosem.cosem.profile_generic import AttributeDescription


class LoRaWANClass(IntEnum):
    CLASS_A = 0
    CLASS_B = 1
    CLASS_C = 2


class LoRaWANVersion(IntEnum):
    V1_0 = 0
    V1_0_1 = 1
    V1_0_2 = 2
    V1_0_3 = 3
    V1_0_4 = 4
    V1_1 = 5


class LoRaBand(IntEnum):
    CN470 = 0
    EU868 = 1
    US915 = 2
    AS923 = 3
    AU915 = 4
    IN865 = 5
    KR920 = 6


@attr.s(auto_attribs=True)
class LoRaWANSetup:
    """COSEM IC LoRaWAN Setup (class_id=107).

    Attributes:
        1: logical_name (static)
        2: dev_eui (static) - Device EUI (8 bytes)
        3: app_eui (static) - Application EUI (8 bytes)
        4: app_key (static) - Application Key (16 bytes)
        5: dev_addr (static) - Device Address (4 bytes)
        6: nwk_skey (static) - Network Session Key
        7: app_skey (static) - Application Session Key
        8: lora_class (static) - Device class (A/B/C)
        9: band (static) - Frequency band
        10: version (static) - LoRaWAN version
        11: adr_enabled (static) - Adaptive Data Rate
        12: confirmed_uplink (static) - Confirmed vs unconfirmed
        13: fcnt_up (dynamic) - Uplink frame counter
        14: fcnt_down (dynamic) - Downlink frame counter
        15: max_payload_size (static) - Max DLMS payload per frame
        16: fragmentation_enabled (static) - Enable DLMS fragmentation
    Methods:
        1: join
        2: reset
        3: set_class
    """

    CLASS_ID: ClassVar[int] = 107
    VERSION: ClassVar[int] = 0

    logical_name: Obis
    dev_eui: Optional[bytes] = None
    app_eui: Optional[bytes] = None
    app_key: Optional[bytes] = None
    dev_addr: Optional[bytes] = None
    nwk_skey: Optional[bytes] = None
    app_skey: Optional[bytes] = None
    lora_class: LoRaWANClass = LoRaWANClass.CLASS_A
    band: LoRaBand = LoRaBand.CN470
    version: LoRaWANVersion = LoRaWANVersion.V1_0_3
    adr_enabled: bool = True
    confirmed_uplink: bool = False
    fcnt_up: int = 0
    fcnt_down: int = 0
    max_payload_size: int = 50  # conservative for CN470
    fragmentation_enabled: bool = True

    STATIC_ATTRIBUTES: ClassVar[Dict[int, AttributeDescription]] = {
        1: AttributeDescription(attribute_id=1, attribute_name="logical_name"),
        2: AttributeDescription(attribute_id=2, attribute_name="dev_eui"),
        3: AttributeDescription(attribute_id=3, attribute_name="app_eui"),
        4: AttributeDescription(attribute_id=4, attribute_name="app_key"),
        5: AttributeDescription(attribute_id=5, attribute_name="dev_addr"),
        6: AttributeDescription(attribute_id=6, attribute_name="nwk_skey"),
        7: AttributeDescription(attribute_id=7, attribute_name="app_skey"),
        8: AttributeDescription(attribute_id=8, attribute_name="lora_class"),
        9: AttributeDescription(attribute_id=9, attribute_name="band"),
        10: AttributeDescription(attribute_id=10, attribute_name="version"),
        11: AttributeDescription(attribute_id=11, attribute_name="adr_enabled"),
        12: AttributeDescription(attribute_id=12, attribute_name="confirmed_uplink"),
        15: AttributeDescription(attribute_id=15, attribute_name="max_payload_size"),
        16: AttributeDescription(attribute_id=16, attribute_name="fragmentation_enabled"),
    }
    DYNAMIC_ATTRIBUTES: ClassVar[Dict[int, AttributeDescription]] = {
        13: AttributeDescription(attribute_id=13, attribute_name="fcnt_up"),
        14: AttributeDescription(attribute_id=14, attribute_name="fcnt_down"),
    }
    METHODS: ClassVar[Dict[int, str]] = {1: "join", 2: "reset", 3: "set_class"}

    def join(self) -> None:
        """Method 1: Initiate OTAA join procedure."""
        self.fcnt_up = 0
        self.fcnt_down = 0

    def reset(self) -> None:
        """Method 2: Reset session."""
        self.fcnt_up = 0
        self.fcnt_down = 0
        self.dev_addr = None
        self.nwk_skey = None
        self.app_skey = None

    def set_class(self, device_class: LoRaWANClass) -> None:
        """Method 3: Change device class."""
        self.lora_class = device_class

    def is_static_attribute(self, attribute_id: int) -> bool:
        return attribute_id in self.STATIC_ATTRIBUTES
