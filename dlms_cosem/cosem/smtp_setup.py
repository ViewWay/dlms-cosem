"""IC class 46 - SMTP Setup.

SMTP (Simple Mail Transfer Protocol) configuration.

Blue Book: DLMS UA 1000-1 Ed. 14, §4.7.6
"""
from typing import Any, ClassVar, Dict, List, Optional

import attr

from dlms_cosem import enumerations as enums
from dlms_cosem.cosem.obis import Obis
from dlms_cosem.cosem.profile_generic import AttributeDescription


@attr.s(auto_attribs=True)
class SMTPSetup:
    """COSEM IC SMTP Setup (class_id=46).

    Attributes:
        1: logical_name (static)
        2: server_address (dynamic) - SMTP server address
        3: server_port (dynamic) - SMTP server port
        4: username (dynamic) - Authentication username
        5: password (dynamic) - Authentication password
        6: use_tls (dynamic) - Whether to use TLS
        7: sender_address (dynamic) - Sender email address
        8: recipient_list (dynamic) - List of recipient addresses
    Methods:
        1: reset
        2: send_test_email
    """

    CLASS_ID: ClassVar[int] = enums.CosemInterface.SMTP_SETUP
    VERSION: ClassVar[int] = 0

    logical_name: Obis
    server_address: str = ""
    server_port: int = 25
    username: str = ""
    password: str = ""
    use_tls: bool = False
    sender_address: str = ""
    recipient_list: List[str] = attr.ib(factory=list)

    STATIC_ATTRIBUTES: ClassVar[Dict[int, AttributeDescription]] = {
        1: AttributeDescription(attribute_id=1, attribute_name="logical_name"),
    }
    DYNAMIC_ATTRIBUTES: ClassVar[Dict[int, AttributeDescription]] = {
        2: AttributeDescription(attribute_id=2, attribute_name="server_address"),
        3: AttributeDescription(attribute_id=3, attribute_name="server_port"),
        4: AttributeDescription(attribute_id=4, attribute_name="username"),
        5: AttributeDescription(attribute_id=5, attribute_name="password"),
        6: AttributeDescription(attribute_id=6, attribute_name="use_tls"),
        7: AttributeDescription(attribute_id=7, attribute_name="sender_address"),
        8: AttributeDescription(attribute_id=8, attribute_name="recipient_list"),
    }
    METHODS: ClassVar[Dict[int, str]] = {
        1: "reset",
        2: "send_test_email",
    }

    def reset(self) -> None:
        """Method 1: Reset SMTP configuration to defaults."""
        self.server_address = ""
        self.server_port = 25
        self.username = ""
        self.password = ""
        self.use_tls = False
        self.sender_address = ""
        self.recipient_list = []

    def send_test_email(self) -> bool:
        """Method 2: Send a test email."""
        # In real implementation, would send test email
        return len(self.server_address) > 0 and len(self.recipient_list) > 0

    def is_static_attribute(self, attribute_id: int) -> bool:
        return attribute_id in self.STATIC_ATTRIBUTES

    def add_recipient(self, email_address: str) -> None:
        """Add a recipient to the list."""
        if email_address not in self.recipient_list:
            self.recipient_list.append(email_address)
