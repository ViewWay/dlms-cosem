"""IC class 70 - Disconnect Control.

Control for disconnecting/reconnecting loads.

Blue Book: DLMS UA 1000-1 Ed. 14, §4.5.8
"""
from typing import ClassVar, Dict, Optional

import attr

from dlms_cosem import enumerations as enums
from dlms_cosem.cosem.obis import Obis
from dlms_cosem.cosem.C5_ProfileGeneric import AttributeDescription


class DisconnectState:
    """Disconnect control states."""
    DISCONNECTED = 0
    CONNECTED = 1
    READY_FOR_RECONNECTION = 2


@attr.s(auto_attribs=True)
class DisconnectControl:
    """COSEM IC Disconnect Control (class_id=70).

    Attributes:
        1: logical_name (static)
        2: output_state (dynamic) - Current state of output
        3: control_state (dynamic) - Control state machine status
        4: control_mode (dynamic) - Control mode configuration
    Methods:
        1: remote_disconnect
        2: remote_reconnect
    """

    CLASS_ID: ClassVar[int] = enums.CosemInterface.DISCONNECT_CONTROL
    VERSION: ClassVar[int] = 0

    logical_name: Obis
    output_state: int = DisconnectState.CONNECTED
    control_state: int = DisconnectState.CONNECTED
    control_mode: int = 0  # Control mode (local/remote/etc)

    STATIC_ATTRIBUTES: ClassVar[Dict[int, AttributeDescription]] = {
        1: AttributeDescription(attribute_id=1, attribute_name="logical_name"),
    }
    DYNAMIC_ATTRIBUTES: ClassVar[Dict[int, AttributeDescription]] = {
        2: AttributeDescription(attribute_id=2, attribute_name="output_state"),
        3: AttributeDescription(attribute_id=3, attribute_name="control_state"),
        4: AttributeDescription(attribute_id=4, attribute_name="control_mode"),
    }
    METHODS: ClassVar[Dict[int, str]] = {
        1: "remote_disconnect",
        2: "remote_reconnect",
    }

    def remote_disconnect(self) -> None:
        """Method 1: Disconnect the load remotely."""
        self.output_state = DisconnectState.DISCONNECTED
        self.control_state = DisconnectState.DISCONNECTED

    def remote_reconnect(self) -> None:
        """Method 2: Reconnect the load remotely."""
        if self.control_state == DisconnectState.READY_FOR_RECONNECTION:
            self.output_state = DisconnectState.CONNECTED
            self.control_state = DisconnectState.CONNECTED

    def is_static_attribute(self, attribute_id: int) -> bool:
        return attribute_id in self.STATIC_ATTRIBUTES

    def is_connected(self) -> bool:
        """Check if load is connected."""
        return self.output_state == DisconnectState.CONNECTED

    def is_disconnected(self) -> bool:
        """Check if load is disconnected."""
        return self.output_state == DisconnectState.DISCONNECTED
