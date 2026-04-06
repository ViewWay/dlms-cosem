"""IC class 71 - Limiter.

Threshold monitoring and limiting for values.

Blue Book: DLMS UA 1000-1 Ed. 14, §4.5.9
"""
from typing import Any, ClassVar, Dict, Optional

import attr

from dlms_cosem import enumerations as enums
from dlms_cosem.cosem.obis import Obis
from dlms_cosem.cosem.C5_ProfileGeneric import AttributeDescription


@attr.s(auto_attribs=True)
class Limiter:
    """COSEM IC Limiter (class_id=71).

    Attributes:
        1: logical_name (static)
        2: monitored_value (dynamic) - Value being monitored
        3: threshold_active (dynamic) - Active threshold value
        4: threshold_normal (dynamic) - Normal threshold value
        5: threshold_emergency (dynamic) - Emergency threshold value
        6: min_over_threshold_duration (dynamic) - Min duration over threshold
        7: min_under_threshold_duration (dynamic) - Min duration under threshold
        8: emergency_profile (dynamic) - Emergency profile settings
        9: emergency_profile_group (dynamic) - Emergency profile group
        10: emergency_profile_active (dynamic) - Is emergency profile active
        11: action_over_threshold (dynamic) - Action when over threshold
        12: action_under_threshold (dynamic) - Action when under threshold
    Methods:
        1: reset
    """

    CLASS_ID: ClassVar[int] = enums.CosemInterface.LIMITER
    VERSION: ClassVar[int] = 0

    logical_name: Obis
    monitored_value: Optional[Dict[str, Any]] = None
    threshold_active: float = 0.0
    threshold_normal: float = 0.0
    threshold_emergency: float = 0.0
    min_over_threshold_duration: int = 0
    min_under_threshold_duration: int = 0
    emergency_profile: Optional[Dict[str, Any]] = None
    emergency_profile_group: int = 0
    emergency_profile_active: bool = False
    action_over_threshold: Optional[Dict[str, Any]] = None
    action_under_threshold: Optional[Dict[str, Any]] = None

    STATIC_ATTRIBUTES: ClassVar[Dict[int, AttributeDescription]] = {
        1: AttributeDescription(attribute_id=1, attribute_name="logical_name"),
    }
    DYNAMIC_ATTRIBUTES: ClassVar[Dict[int, AttributeDescription]] = {
        2: AttributeDescription(attribute_id=2, attribute_name="monitored_value"),
        3: AttributeDescription(attribute_id=3, attribute_name="threshold_active"),
        4: AttributeDescription(attribute_id=4, attribute_name="threshold_normal"),
        5: AttributeDescription(attribute_id=5, attribute_name="threshold_emergency"),
        6: AttributeDescription(attribute_id=6, attribute_name="min_over_threshold_duration"),
        7: AttributeDescription(attribute_id=7, attribute_name="min_under_threshold_duration"),
        8: AttributeDescription(attribute_id=8, attribute_name="emergency_profile"),
        9: AttributeDescription(attribute_id=9, attribute_name="emergency_profile_group"),
        10: AttributeDescription(attribute_id=10, attribute_name="emergency_profile_active"),
        11: AttributeDescription(attribute_id=11, attribute_name="action_over_threshold"),
        12: AttributeDescription(attribute_id=12, attribute_name="action_under_threshold"),
    }
    METHODS: ClassVar[Dict[int, str]] = {1: "reset"}

    def reset(self) -> None:
        """Method 1: Reset limiter to defaults."""
        self.threshold_active = 0.0
        self.threshold_normal = 0.0
        self.threshold_emergency = 0.0
        self.min_over_threshold_duration = 0
        self.min_under_threshold_duration = 0
        self.emergency_profile_active = False

    def is_static_attribute(self, attribute_id: int) -> bool:
        return attribute_id in self.STATIC_ATTRIBUTES

    def is_over_threshold(self, value: float) -> bool:
        """Check if value exceeds active threshold."""
        return value > self.threshold_active

    def is_under_threshold(self, value: float) -> bool:
        """Check if value is below threshold."""
        return value < self.threshold_normal
