"""IC class 124 - Communication Port Protection.

Protects communication ports from unauthorized access and attacks.
Implements port-level security and access control.

Blue Book: DLMS UA 1000-1 Ed. 14, §4.2.124
"""
from typing import ClassVar, Dict, List

import attr

from dlms_cosem import enumerations as enums
from dlms_cosem.cosem.obis import Obis
from dlms_cosem.cosem.profile_generic import AttributeDescription


@attr.s(auto_attribs=True)
class ProtectedPort:
    """A protected communication port."""
    port_id: int
    access_level: int = 1
    max_connections: int = 5
    timeout_seconds: int = 300
    allowed_methods: List[int] = attr.ib(factory=list)


@attr.s(auto_attribs=True)
class CommPortProtection:
    """COSEM IC Communication Port Protection (class_id=124).

    Attributes:
        1: logical_name (static)
        2: protected_ports (dynamic, array of ProtectedPort)
        3: default_protection_level (dynamic, unsigned)
        4: protection_enabled (dynamic, boolean)
    Methods:
        1: add_port_protection
        2: remove_port_protection
        3: check_port_access
        4: set_port_timeout
    """

    CLASS_ID: ClassVar[int] = enums.CosemInterface.COMMUNICATION_PORT_PROTECTION
    VERSION: ClassVar[int] = 0

    logical_name: Obis
    protected_ports: List[ProtectedPort] = attr.ib(factory=list)
    default_protection_level: int = 1
    protection_enabled: bool = True

    STATIC_ATTRIBUTES: ClassVar[Dict[int, AttributeDescription]] = {
        1: AttributeDescription(attribute_id=1, attribute_name="logical_name"),
    }
    DYNAMIC_ATTRIBUTES: ClassVar[Dict[int, AttributeDescription]] = {
        2: AttributeDescription(attribute_id=2, attribute_name="protected_ports"),
        3: AttributeDescription(attribute_id=3, attribute_name="default_protection_level"),
        4: AttributeDescription(attribute_id=4, attribute_name="protection_enabled"),
    }
    METHODS: ClassVar[Dict[int, str]] = {
        1: "add_port_protection",
        2: "remove_port_protection",
        3: "check_port_access",
        4: "set_port_timeout",
    }

    def add_port_protection(self, port_id: int, access_level: int = 1, max_connections: int = 5) -> None:
        """Method 1: Add protection for a port."""
        port = ProtectedPort(
            port_id=port_id,
            access_level=access_level,
            max_connections=max_connections,
            timeout_seconds=300,
            allowed_methods=[],
        )
        self.protected_ports.append(port)

    def remove_port_protection(self, port_id: int) -> bool:
        """Method 2: Remove protection for a port."""
        for i, port in enumerate(self.protected_ports):
            if port.port_id == port_id:
                self.protected_ports.pop(i)
                return True
        return False

    def check_port_access(self, port_id: int, user_level: int) -> bool:
        """Method 3: Check if access to port is allowed."""
        if not self.protection_enabled:
            return True

        port = self.get_port(port_id)
        if port is None:
            # Port not in protected list, use default
            return user_level >= self.default_protection_level

        return user_level >= port.access_level

    def set_port_timeout(self, port_id: int, timeout_seconds: int) -> bool:
        """Method 4: Set timeout for a port."""
        port = self.get_port(port_id)
        if port is not None:
            port.timeout_seconds = max(0, timeout_seconds)
            return True
        return False

    def get_port(self, port_id: int) -> ProtectedPort:
        """Get port by ID."""
        for port in self.protected_ports:
            if port.port_id == port_id:
                return port
        return None

    def set_default_protection_level(self, level: int) -> None:
        """Set the default protection level."""
        self.default_protection_level = max(0, min(255, level))

    def set_protection_enabled(self, enabled: bool) -> None:
        """Enable or disable protection."""
        self.protection_enabled = enabled

    def add_allowed_method(self, port_id: int, method_id: int) -> bool:
        """Add an allowed method for a port."""
        port = self.get_port(port_id)
        if port is not None:
            port.allowed_methods.append(method_id)
            return True
        return False

    def get_protected_port_count(self) -> int:
        """Get the number of protected ports."""
        return len(self.protected_ports)

    def clear_protections(self) -> None:
        """Clear all port protections."""
        self.protected_ports = []

    def is_static_attribute(self, attribute_id: int) -> bool:
        return attribute_id in self.STATIC_ATTRIBUTES
