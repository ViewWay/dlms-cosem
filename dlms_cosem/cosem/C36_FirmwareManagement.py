"""IC class 36 - Firmware Management.

Manages firmware updates and versions for metering devices.

Blue Book: DLMS UA 1000-1 Ed. 14

Attributes:
    1: logical_name (static)
    2: firmware_information (static)
    3: firmware_image_to_activate_info (static)
    4: firmware_image_active_info (static)
    5: firmware_image_to_activate (dynamic)
    6: firmware_image_active (dynamic)
    7: activate_firmware_image (method)
    8: active_firmware_image_signature (dynamic)
"""
from typing import ClassVar, List, Optional

import attr

from dlms_cosem import enumerations as enums
from dlms_cosem.cosem.obis import Obis


@attr.s(auto_attribs=True)
class FirmwareComponent:
    """Firmware component information."""
    component_id: int = 0
    version: str = ""
    status: int = 0


@attr.s(auto_attribs=True)
class FirmwareManagement:
    """COSEM IC Firmware Management (class_id=36).

    Attributes:
        1: logical_name (static)
        2: firmware_information (static)
        3: firmware_image_to_activate_info (static)
        4: firmware_image_active_info (static)
        5: firmware_image_to_activate (dynamic)
        6: firmware_image_active (dynamic)
    """

    CLASS_ID: ClassVar[int] = enums.CosemInterface.FIRMWARE_MANAGEMENT
    VERSION: ClassVar[int] = 0

    logical_name: Obis
    firmware_information: Optional[List[FirmwareComponent]] = None
    update_pending: bool = False
    current_operation: int = 0
