"""SML (Smart Message Language) parser for German/European meters.

SML is used by German/European energy meters as defined in
BSI TR-03109 and EDL 21.

This module provides lazy-loaded imports to reduce memory footprint.
"""
from __future__ import annotations

__all__ = [
    "SMLParser",
    "SMLFile",
    "SMLMessage",
    "SMLValueEntry",
    "SMLPublicKey",
    "SMLTag",
    "SMLType",
    "SMLSignatureMode",
    "SMLToDLMSBridge",
]


def __getattr__(name: str):
    """Lazy import SML classes on first access."""
    if name == "SMLParser":
        from dlms_cosem.sml.parser import SMLParser
        return SMLParser
    if name == "SMLFile":
        from dlms_cosem.sml.models import SMLFile
        return SMLFile
    if name == "SMLMessage":
        from dlms_cosem.sml.models import SMLMessage
        return SMLMessage
    if name == "SMLValueEntry":
        from dlms_cosem.sml.models import SMLValueEntry
        return SMLValueEntry
    if name == "SMLPublicKey":
        from dlms_cosem.sml.models import SMLPublicKey
        return SMLPublicKey
    if name == "SMLTag":
        from dlms_cosem.sml.types import SMLTag
        return SMLTag
    if name == "SMLType":
        from dlms_cosem.sml.types import SMLType
        return SMLType
    if name == "SMLSignatureMode":
        from dlms_cosem.sml.types import SMLSignatureMode
        return SMLSignatureMode
    if name == "SMLToDLMSBridge":
        from dlms_cosem.sml.bridge import SMLToDLMSBridge
        return SMLToDLMSBridge

    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
