"""IC class 9 - Script Table.

Contains scripts (sequences of actions) to be executed. Scripts can be
triggered by other objects (e.g., schedules, register monitors).

Blue Book: DLMS UA 1000-1 Ed. 14, §4.2.10
"""
from typing import Any, ClassVar, Dict, List, Optional

import attr

from dlms_cosem import enumerations as enums
from dlms_cosem.cosem.obis import Obis
from dlms_cosem.cosem.C7_ProfileGeneric import AttributeDescription


@attr.s(auto_attribs=True)
class ScriptTable:
    """COSEM IC Script Table (class_id=9).

    Attributes:
        1: logical_name (static)
        2: scripts (static) - list of scripts, each a list of CosemMethod
    Methods:
        1: execute_script
    """

    CLASS_ID: ClassVar[int] = enums.CosemInterface.SCRIPT_TABLE
    VERSION: ClassVar[int] = 0

    logical_name: Obis
    scripts: List[List[Any]] = attr.ib(factory=list)

    STATIC_ATTRIBUTES: ClassVar[Dict[int, AttributeDescription]] = {
        1: AttributeDescription(attribute_id=1, attribute_name="logical_name"),
        2: AttributeDescription(attribute_id=2, attribute_name="scripts"),
    }
    DYNAMIC_ATTRIBUTES: ClassVar[Dict[int, AttributeDescription]] = {}
    METHODS: ClassVar[Dict[int, str]] = {1: "execute_script"}

    def execute_script(self, script_identifier: int) -> None:
        """Method 1: Execute a script by its identifier."""
        if script_identifier < len(self.scripts):
            pass  # execute the script actions

    def is_static_attribute(self, attribute_id: int) -> bool:
        return attribute_id in self.STATIC_ATTRIBUTES
