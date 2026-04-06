"""IC023 - Load Profile Switch.

Controls which load profile (billing, daily, etc.) is currently active
and manages profile switching based on tariff transitions.

Blue Book: DLMS UA 1000-1 Ed. 14
"""
from datetime import datetime
from typing import Any, ClassVar, Dict, List, Optional

import attr

from dlms_cosem import enumerations as enums
from dlms_cosem.cosem.obis import Obis
from dlms_cosem.cosem.C7_ProfileGeneric import AttributeDescription


@attr.s(auto_attribs=True)
class LoadProfileSwitch:
    """COSEM IC Load Profile Switch (class_id=23).

    Attributes:
        1: logical_name (static)
        2: current_profile (dynamic)
        3: profile_list (static, list of profile definitions)
        4: switch_time (dynamic, datetime)
        5: switch_active (dynamic, boolean)
    Methods:
        1: switch_profile
        2: add_profile
    """

    CLASS_ID: ClassVar[int] = 23
    VERSION: ClassVar[int] = 0

    logical_name: Obis
    current_profile: int = 0
    profile_list: List[Dict[str, Any]] = attr.ib(factory=list)
    switch_time: Optional[datetime] = None
    switch_active: bool = True

    STATIC_ATTRIBUTES: ClassVar[Dict[int, AttributeDescription]] = {
        1: AttributeDescription(attribute_id=1, attribute_name="logical_name"),
        3: AttributeDescription(attribute_id=3, attribute_name="profile_list"),
    }
    DYNAMIC_ATTRIBUTES: ClassVar[Dict[int, AttributeDescription]] = {
        2: AttributeDescription(attribute_id=2, attribute_name="current_profile"),
        4: AttributeDescription(attribute_id=4, attribute_name="switch_time"),
        5: AttributeDescription(attribute_id=5, attribute_name="switch_active"),
    }
    METHODS: ClassVar[Dict[int, str]] = {1: "switch_profile", 2: "add_profile"}

    def switch_profile(self, profile_index: int) -> None:
        if 0 <= profile_index < len(self.profile_list):
            self.current_profile = profile_index
            self.switch_time = datetime.now()

    def add_profile(self, name: str, obis: str) -> int:
        profile = {"name": name, "obis": obis, "index": len(self.profile_list)}
        self.profile_list.append(profile)
        return len(self.profile_list) - 1

    def is_static_attribute(self, attribute_id: int) -> bool:
        return attribute_id in self.STATIC_ATTRIBUTES
