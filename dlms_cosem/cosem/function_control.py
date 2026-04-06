"""IC class 122 - Function Control.

Controls the execution of functions and methods on COSEM objects.
Manages function scheduling and execution policies.

Blue Book: DLMS UA 1000-1 Ed. 14, §4.2.122
"""
from typing import ClassVar, Dict, List, Optional

import attr

from dlms_cosem import enumerations as enums
from dlms_cosem.cosem.obis import Obis
from dlms_cosem.cosem.profile_generic import AttributeDescription


@attr.s(auto_attribs=True)
class FunctionControlEntry:
    """A function control entry."""
    function_name: str
    object_reference: bytes
    method_id: int
    enabled: bool = True
    schedule: Optional[str] = None


@attr.s(auto_attribs=True)
class FunctionControl:
    """COSEM IC Function Control (class_id=122).

    Attributes:
        1: logical_name (static)
        2: functions (dynamic, array of FunctionControlEntry)
        3: execution_policy (dynamic, enum)
        4: max_concurrent_executions (dynamic, unsigned)
    Methods:
        1: add_function
        2: remove_function
        3: enable_function
        4: disable_function
        5: execute_function
    """

    CLASS_ID: ClassVar[int] = enums.CosemInterface.FUNCTION_CONTROL
    VERSION: ClassVar[int] = 0

    logical_name: Obis
    functions: List[FunctionControlEntry] = attr.ib(factory=list)
    execution_policy: int = 0  # 0: sequential, 1: parallel, 2: priority
    max_concurrent_executions: int = 1

    STATIC_ATTRIBUTES: ClassVar[Dict[int, AttributeDescription]] = {
        1: AttributeDescription(attribute_id=1, attribute_name="logical_name"),
    }
    DYNAMIC_ATTRIBUTES: ClassVar[Dict[int, AttributeDescription]] = {
        2: AttributeDescription(attribute_id=2, attribute_name="functions"),
        3: AttributeDescription(attribute_id=3, attribute_name="execution_policy"),
        4: AttributeDescription(attribute_id=4, attribute_name="max_concurrent_executions"),
    }
    METHODS: ClassVar[Dict[int, str]] = {
        1: "add_function",
        2: "remove_function",
        3: "enable_function",
        4: "disable_function",
        5: "execute_function",
    }

    def add_function(self, name: str, obj_ref: bytes, method_id: int, schedule: Optional[str] = None) -> None:
        """Method 1: Add a function to control."""
        entry = FunctionControlEntry(
            function_name=name,
            object_reference=obj_ref,
            method_id=method_id,
            enabled=True,
            schedule=schedule,
        )
        self.functions.append(entry)

    def remove_function(self, name: str) -> bool:
        """Method 2: Remove a function."""
        for i, func in enumerate(self.functions):
            if func.function_name == name:
                self.functions.pop(i)
                return True
        return False

    def enable_function(self, name: str) -> bool:
        """Method 3: Enable a function."""
        for func in self.functions:
            if func.function_name == name:
                func.enabled = True
                return True
        return False

    def disable_function(self, name: str) -> bool:
        """Method 4: Disable a function."""
        for func in self.functions:
            if func.function_name == name:
                func.enabled = False
                return True
        return False

    def execute_function(self, name: str, parameters: Optional[bytes] = None) -> bool:
        """Method 5: Execute a function."""
        for func in self.functions:
            if func.function_name == name and func.enabled:
                # In a real implementation, would execute the method on the object
                return True
        return False

    def get_function_by_name(self, name: str) -> Optional[FunctionControlEntry]:
        """Get a function by name."""
        for func in self.functions:
            if func.function_name == name:
                return func
        return None

    def set_execution_policy(self, policy: int) -> None:
        """Set the execution policy (0: sequential, 1: parallel, 2: priority)."""
        self.execution_policy = max(0, min(2, policy))

    def set_max_concurrent_executions(self, max_exec: int) -> None:
        """Set the maximum number of concurrent executions."""
        self.max_concurrent_executions = max(1, max_exec)

    def get_enabled_function_count(self) -> int:
        """Get the number of enabled functions."""
        return sum(1 for func in self.functions if func.enabled)

    def is_function_enabled(self, name: str) -> bool:
        """Check if a function is enabled."""
        func = self.get_function_by_name(name)
        return func is not None and func.enabled

    def clear_functions(self) -> None:
        """Clear all functions."""
        self.functions = []

    def is_static_attribute(self, attribute_id: int) -> bool:
        return attribute_id in self.STATIC_ATTRIBUTES
