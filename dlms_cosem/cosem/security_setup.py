"""IC class 64 - Security Setup.

Defines security parameters for DLMS/COSEM communication.
Supports SM4-GMAC/SM4-GCM for Chinese national cryptography.

Blue Book: DLMS UA 1000-1 Ed. 14, §4.3.17
Yellow Book: DLMS UA 1000-5
"""
from enum import IntEnum
from typing import Any, ClassVar, Dict, List, Optional

import attr

from dlms_cosem import enumerations as enums
from dlms_cosem.cosem.obis import Obis
from dlms_cosem.cosem.profile_generic import AttributeDescription


class SecurityPolicy(IntEnum):
    """Security policy levels."""
    NONE = 0
    AUTHENTICATED_ONLY = 1
    ENCRYPTED_ONLY = 2
    AUTHENTICATED_ENCRYPTED = 3
    CERTIFICATE_BASED = 4
    DIGITALLY_SIGNED = 5


class CipherAlgorithm(IntEnum):
    """Supported cipher algorithms."""
    AES_128_GCM = 0
    AES_256_GCM = 1
    SM4_GCM = 2
    SM4_GMAC = 3


@attr.s(auto_attribs=True)
class SecuritySetup:
    """COSEM IC Security Setup (class_id=64).

    Attributes:
        1: logical_name (static)
        2: security_policy (static)
        3: security_suite (static) - 0~5
        4: cipher_algorithm (static)
        5: authentication_key (static) - handled via key management
        6: encryption_key (static)
        7: master_key (static)
        8: system_title (static, 8 bytes)
        9: certificate_info (static)
        10: legal_vote (static)
        11: ciphered_legal_vote (static)
    Methods:
        1: add_key
        2: remove_key
        3: change_key
        4: add_certificate
        5: remove_certificate
        6: add_legal_vote
    """

    CLASS_ID: ClassVar[int] = enums.CosemInterface.SECURITY_SETUP
    VERSION: ClassVar[int] = 0

    logical_name: Obis
    security_policy: SecurityPolicy = SecurityPolicy.AUTHENTICATED_ENCRYPTED
    security_suite: int = 0
    cipher_algorithm: CipherAlgorithm = CipherAlgorithm.AES_128_GCM
    authentication_key: Optional[bytes] = None
    encryption_key: Optional[bytes] = None
    master_key: Optional[bytes] = None
    system_title: Optional[bytes] = None
    certificate_info: Optional[bytes] = None
    legal_vote: Optional[bytes] = None
    ciphered_legal_vote: Optional[bytes] = None

    STATIC_ATTRIBUTES: ClassVar[Dict[int, AttributeDescription]] = {
        1: AttributeDescription(attribute_id=1, attribute_name="logical_name"),
        2: AttributeDescription(attribute_id=2, attribute_name="security_policy"),
        3: AttributeDescription(attribute_id=3, attribute_name="security_suite"),
        4: AttributeDescription(attribute_id=4, attribute_name="cipher_algorithm"),
        5: AttributeDescription(attribute_id=5, attribute_name="authentication_key"),
        6: AttributeDescription(attribute_id=6, attribute_name="encryption_key"),
        7: AttributeDescription(attribute_id=7, attribute_name="master_key"),
        8: AttributeDescription(attribute_id=8, attribute_name="system_title"),
        9: AttributeDescription(attribute_id=9, attribute_name="certificate_info"),
        10: AttributeDescription(attribute_id=10, attribute_name="legal_vote"),
    }
    DYNAMIC_ATTRIBUTES: ClassVar[Dict[int, AttributeDescription]] = {
        11: AttributeDescription(attribute_id=11, attribute_name="ciphered_legal_vote"),
    }
    METHODS: ClassVar[Dict[int, str]] = {
        1: "add_key", 2: "remove_key", 3: "change_key",
        4: "add_certificate", 5: "remove_certificate", 6: "add_legal_vote",
    }

    def add_key(self, key: bytes) -> None:
        pass

    def remove_key(self, key_id: int) -> None:
        pass

    def change_key(self, key_id: int, new_key: bytes) -> None:
        pass

    def add_certificate(self, certificate: bytes) -> None:
        pass

    def remove_certificate(self, cert_id: int) -> None:
        pass

    def add_legal_vote(self, vote: bytes) -> None:
        pass

    def is_static_attribute(self, attribute_id: int) -> bool:
        return attribute_id in self.STATIC_ATTRIBUTES
