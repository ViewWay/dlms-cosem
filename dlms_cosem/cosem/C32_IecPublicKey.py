"""IC class 90 - IEC Public Key.

Public key management for cryptographic operations.
Used in security-sensitive metering applications.

Blue Book: IEC 62056-6-2, §4.2.90
"""
from typing import ClassVar, Dict

import attr

from dlms_cosem import enumerations as enums
from dlms_cosem.cosem.obis import Obis
from dlms_cosem.cosem.C5_ProfileGeneric import AttributeDescription


class KeyAlgorithm:
    """Key algorithm types."""
    RSA = 0
    ECC = 1
    AES = 2
    OTHER = 255


class KeyUsage:
    """Key usage flags."""
    ENCRYPTION = 0
    SIGNATURE = 1
    BOTH = 2


@attr.s(auto_attribs=True)
class IecPublicKey:
    """COSEM IC IEC Public Key (class_id=90).

    Attributes:
        1: logical_name (static)
        2: public_key (dynamic, octet-string)
        3: key_id (dynamic, visible-string)
        4: algorithm (dynamic, enum)
        5: key_usage (dynamic, enum)
    Methods:
        1: validate
    """

    CLASS_ID: ClassVar[int] = enums.CosemInterface.IEC_PUBLIC_KEY
    VERSION: ClassVar[int] = 0

    logical_name: Obis
    public_key: bytes = b""
    key_id: str = ""
    algorithm: int = KeyAlgorithm.RSA
    key_usage: int = KeyUsage.BOTH

    STATIC_ATTRIBUTES: ClassVar[Dict[int, AttributeDescription]] = {
        1: AttributeDescription(attribute_id=1, attribute_name="logical_name"),
    }
    DYNAMIC_ATTRIBUTES: ClassVar[Dict[int, AttributeDescription]] = {
        2: AttributeDescription(attribute_id=2, attribute_name="public_key"),
        3: AttributeDescription(attribute_id=3, attribute_name="key_id"),
        4: AttributeDescription(attribute_id=4, attribute_name="algorithm"),
        5: AttributeDescription(attribute_id=5, attribute_name="key_usage"),
    }
    METHODS: ClassVar[Dict[int, str]] = {1: "validate"}

    def validate(self) -> bool:
        """Method 1: Validate the public key."""
        return len(self.public_key) > 0 and len(self.key_id) > 0

    def is_valid(self) -> bool:
        """Check if the key is valid."""
        return self.validate()

    def set_algorithm(self, algorithm: int) -> None:
        """Set the key algorithm."""
        self.algorithm = algorithm

    def get_algorithm_name(self) -> str:
        """Get the algorithm name as string."""
        names = {
            KeyAlgorithm.RSA: "RSA",
            KeyAlgorithm.ECC: "ECC",
            KeyAlgorithm.AES: "AES",
            KeyAlgorithm.OTHER: "Other",
        }
        return names.get(self.algorithm, "Unknown")

    def set_key_usage(self, usage: int) -> None:
        """Set the key usage."""
        self.key_usage = usage

    def get_key_usage_name(self) -> str:
        """Get the key usage name as string."""
        names = {
            KeyUsage.ENCRYPTION: "Encryption",
            KeyUsage.SIGNATURE: "Signature",
            KeyUsage.BOTH: "Both",
        }
        return names.get(self.key_usage, "Unknown")

    def is_static_attribute(self, attribute_id: int) -> bool:
        return attribute_id in self.STATIC_ATTRIBUTES
