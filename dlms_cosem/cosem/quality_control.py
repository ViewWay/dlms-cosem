"""IC031 - Quality Control.

Marks measurement data with quality flags (valid/invalid/suspect/estimated).
Used for data validation in billing and load profile data.

Blue Book: DLMS UA 1000-1 Ed. 14
"""
from datetime import datetime
from typing import Any, ClassVar, Dict, List, Optional

import attr

from dlms_cosem import enumerations as enums
from dlms_cosem.cosem.obis import Obis
from dlms_cosem.cosem.profile_generic import AttributeDescription


class QualityFlag:
    """Quality flag bits."""
    VALID = 0x00
    INVALID = 0x01
    SUSPECT = 0x02
    ESTIMATED = 0x04
    POWER_FAILURE = 0x08
    CLOCK_ADJUSTED = 0x10
    DATA_OVERRUN = 0x20
    TEST_MODE = 0x40


@attr.s(auto_attribs=True)
class QualityControl:
    """COSEM IC Quality Control (class_id=31).

    Attributes:
        1: logical_name (static)
        2: quality_flags (dynamic, bitstring)
        3: quality_description (static, string)
        4: quality_timestamp (dynamic)
        5: quality_code_map (static)
    Methods:
        1: reset
        2: set_quality
    """

    CLASS_ID: ClassVar[int] = 31
    VERSION: ClassVar[int] = 0

    logical_name: Obis
    quality_flags: int = QualityFlag.VALID
    quality_description: str = ""
    quality_timestamp: Optional[datetime] = None
    quality_code_map: Dict[int, str] = attr.ib(factory=dict)

    STATIC_ATTRIBUTES: ClassVar[Dict[int, AttributeDescription]] = {
        1: AttributeDescription(attribute_id=1, attribute_name="logical_name"),
        3: AttributeDescription(attribute_id=3, attribute_name="quality_description"),
        5: AttributeDescription(attribute_id=5, attribute_name="quality_code_map"),
    }
    DYNAMIC_ATTRIBUTES: ClassVar[Dict[int, AttributeDescription]] = {
        2: AttributeDescription(attribute_id=2, attribute_name="quality_flags"),
        4: AttributeDescription(attribute_id=4, attribute_name="quality_timestamp"),
    }
    METHODS: ClassVar[Dict[int, str]] = {1: "reset", 2: "set_quality"}

    def set_quality(self, flags: int, description: str = "",
                    timestamp: Optional[datetime] = None) -> None:
        self.quality_flags = flags
        self.quality_description = description
        self.quality_timestamp = timestamp or datetime.now()

    def is_valid(self) -> bool:
        return self.quality_flags == QualityFlag.VALID

    def has_flag(self, flag: int) -> bool:
        return bool(self.quality_flags & flag)

    def reset(self) -> None:
        self.quality_flags = QualityFlag.VALID
        self.quality_description = ""
        self.quality_timestamp = None

    def is_static_attribute(self, attribute_id: int) -> bool:
        return attribute_id in self.STATIC_ATTRIBUTES
