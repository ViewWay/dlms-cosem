"""IC class 76 - DLMSMBusPortSetup.

DLMS/COSEM Server M-Bus Port Setup - DLMS server on M-Bus port.

Blue Book: DLMS UA 1000-1 Ed. 16, class_id=76
"""
from typing import Any, ClassVar, Dict, List, Optional

import attr

from dlms_cosem import enumerations as enums
from dlms_cosem.cosem.obis import Obis


@attr.s(auto_attribs=True)
class DLMSMBusPortSetup:
    """COSEM IC DLMSMBusPortSetup (class_id=76).

    Attributes:
        1: logical_name (static)
        2: m_bus_port_reference (dynamic)
        3: listen_port (dynamic)
        4: slave_devices (dynamic)
        5: client_active (dynamic)
    Methods:
        1: capture
        2: transfer
        3: synchronize_time
        4: initialize
    """

    CLASS_ID: ClassVar[int] = enums.CosemInterface.MBUS_PORT_SETUP_DLMS_COSEM_SERVER
    VERSION: ClassVar[int] = 0

    logical_name: Obis
    m_bus_port_reference: Optional[str] = ''
    listen_port: Optional[int] = 0
    slave_devices: List[Any] = attr.ib(factory=list)
    client_active: Optional[bool] = False

    STATIC_ATTRIBUTES: ClassVar[Dict[int, str]] = {1: "logical_name"}
    DYNAMIC_ATTRIBUTES: ClassVar[Dict[int, str]] = {2: 'm_bus_port_reference', 3: 'listen_port', 4: 'slave_devices', 5: 'client_active'}
    METHODS: ClassVar[Dict[int, str]] = {1: 'capture', 2: 'transfer', 3: 'synchronize_time', 4: 'initialize'}

    def capture(self) -> None:
        """Method 1: capture."""

    def transfer(self) -> None:
        """Method 2: transfer."""

    def synchronize_time(self) -> None:
        """Method 3: synchronize_time."""

    def initialize(self) -> None:
        """Method 4: initialize."""

    def is_static_attribute(self, attribute_id: int) -> bool:
        return attribute_id in self.STATIC_ATTRIBUTES

