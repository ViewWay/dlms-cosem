"""SML data models."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, List, Optional

from dlms_cosem.sml.types import SMLSignatureMode, SMLTag


@dataclass
class SMLPublicKey:
    """SML public key information."""
    key_type: int = 0
    key_value: bytes = b""
    key_exp: int = 65537
    signature_mode: SMLSignatureMode = SMLSignatureMode.NONE

    @property
    def fingerprint(self) -> str:
        import hashlib
        return hashlib.sha256(self.key_value).hexdigest()

    def verify(self, data: bytes, signature: bytes) -> bool:
        """Verify data signature."""
        if self.signature_mode == SMLSignatureMode.NONE:
            return True
        # Placeholder - real implementation needs cryptography lib
        return False


@dataclass
class SMLValueEntry:
    """A single SML value entry from a value list."""
    obis: bytes
    value: Any
    unit: Optional[int] = None
    scaler: Optional[int] = None
    status: Optional[int] = None
    timestamp: Optional[int] = None

    @property
    def obis_str(self) -> str:
        parts = list(self.obis)
        return f"{parts[0]}.{parts[1]}.{parts[2]}.{parts[3]}.{parts[4]}.{parts[5]}"


@dataclass
class SMLMessage:
    """Parsed SML message."""
    tag: SMLTag
    transaction_id: bytes = b""
    group_no: int = 0
    abort_on_error: int = 0
    body: Optional[Any] = None
    crc: Optional[int] = None


@dataclass
class SMLFile:
    """Complete SML file with messages."""
    messages: List[SMLMessage] = field(default_factory=list)
    public_key: Optional[SMLPublicKey] = None

    def get_value_entries(self) -> List[SMLValueEntry]:
        """Extract all value entries from profile list responses."""
        entries = []
        for msg in self.messages:
            if msg.tag == SMLTag.GET_PROFILE_LIST_RESPONSE:
                entries.extend(self._extract_entries(msg.body))
        return entries

    @staticmethod
    def _extract_entries(body: Any) -> List[SMLValueEntry]:
        """Extract value entries from response body."""
        entries = []
        if isinstance(body, list) and len(body) > 1:
            value_list = body[1]
            if isinstance(value_list, list):
                for entry in value_list:
                    if isinstance(entry, list) and len(entry) >= 2:
                        obis = entry[0] if isinstance(entry[0], bytes) else b"\x00" * 6
                        value = entry[1] if len(entry) > 1 else None
                        scaler = entry[2] if len(entry) > 2 else None
                        unit = entry[3] if len(entry) > 3 else None
                        entries.append(SMLValueEntry(
                            obis=obis,
                            value=value,
                            scaler=scaler,
                            unit=unit,
                        ))
        return entries
