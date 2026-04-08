"""
Key format conversion utilities for DLMS/COSEM.

Supports multiple formats with automatic detection:
- hex:00112233... or 00112233...
- base64:ABC123... or ABC123...
- Raw bytes
"""
import base64
from enum import Enum
from typing import Literal


class KeyFormat(str, Enum):
    """Key format types for encoding and decoding."""

    RAW = "raw"
    HEX = "hex"
    BASE64 = "base64"
    PEM = "pem"


class KeyFormatter:
    """
    Format conversion for cryptographic keys.

    Supports multiple formats with automatic detection:
    - hex:00112233... or 00112233...
    - base64:ABC123... or ABC123...
    - Raw bytes
    """

    @staticmethod
    def encode(
        key: bytes, format: KeyFormat | Literal["raw", "hex", "base64"], uppercase: bool = False
    ) -> str:
        """
        Encode a key to the specified format.

        Args:
            key: Key bytes to encode
            format: Target format
            uppercase: For hex, use uppercase letters

        Returns:
            Encoded key string
        """
        format = KeyFormat(format)

        if format == KeyFormat.HEX:
            result = key.hex()
            return result.upper() if uppercase else result
        elif format == KeyFormat.BASE64:
            return base64.b64encode(key).decode()
        elif format == KeyFormat.RAW:
            return key.decode("latin1") if isinstance(key, bytes) else key
        else:
            raise ValueError(f"Unsupported format: {format}")

    @staticmethod
    def decode(data: str | bytes) -> bytes:
        """
        Decode a key from string or bytes.

        Automatically detects format from prefix:
        - "hex:..." for hexadecimal
        - "base64:..." for Base64
        - Otherwise attempts auto-detection

        Args:
            data: Key data to decode

        Returns:
            Decoded key bytes
        """
        if isinstance(data, bytes):
            return data

        data = data.strip()

        # Check for explicit prefix
        if data.startswith("hex:"):
            return bytes.fromhex(data[4:])
        elif data.startswith("base64:"):
            return base64.b64decode(data[7:])

        # Auto-detect
        # Try hex first (even length, valid hex chars)
        if len(data) % 2 == 0:
            try:
                return bytes.fromhex(data)
            except ValueError:
                pass

        # Try base64
        try:
            return base64.b64decode(data)
        except Exception:
            pass

        raise ValueError(
            f"Cannot decode key data: {data[:20]}... "
            f"Use 'hex:...' or 'base64:...' prefix to specify format"
        )

    @staticmethod
    def format_key(
        key: bytes, format: Literal["hex", "base64"] = "hex", prefix: bool = True
    ) -> str:
        """
        Format a key with optional prefix.

        Args:
            key: Key bytes to format
            format: Target format ("hex" or "base64")
            prefix: Whether to add format prefix

        Returns:
            Formatted key string
        """
        encoded = KeyFormatter.encode(key, KeyFormat(format))
        if prefix:
            return f"{format}:{encoded}"
        return encoded
