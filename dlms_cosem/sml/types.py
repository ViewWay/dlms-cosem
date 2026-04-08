"""SML (Smart Message Language) type definitions.

SML is used by German/European energy meters as defined in
BSI TR-03109 and EDL 21.
"""
from __future__ import annotations

from enum import IntEnum


class SMLTag(IntEnum):
    """SML TLV tags."""
    END_OF_SML_FILE = 0x1b
    GET_OPEN_REQUEST = 0x01
    GET_OPEN_RESPONSE = 0x02
    GET_CLOSE_REQUEST = 0x03
    GET_CLOSE_RESPONSE = 0x04
    GET_PROFILE_LIST_REQUEST = 0x05
    GET_PROFILE_LIST_RESPONSE = 0x06
    GET_PROC_PARAMETER_REQUEST = 0x07
    GET_PROC_PARAMETER_RESPONSE = 0x08
    SET_PROC_PARAMETER_REQUEST = 0x09
    ATTENTION_RESPONSE = 0x10

    # Sub-tags
    PUBLIC_KEY = 0x01
    PUBLIC_KEY_SIGNATURE = 0x02
    SERVER_ID = 0x01
    CLIENT_ID = 0x02
    VALUE_LIST = 0x76
    ENTRY = 0x77
    SCALER_UNIT = 0x52
    VALUE = 0x63


class SMLType(IntEnum):
    """SML value types."""
    OCTET_STRING = 0x01
    INTEGER_8 = 0x02
    INTEGER_16 = 0x03
    INTEGER_32 = 0x05
    INTEGER_64 = 0x09
    UNSIGNED_8 = 0x10
    UNSIGNED_16 = 0x11
    UNSIGNED_32 = 0x13
    UNSIGNED_64 = 0x17
    BOOLEAN = 0x21
    BITSTRING = 0x22
    BCD = 0x41
    LIST = 0x70  # variable length
    LIST_WITH_LENGTH = 0x71  # 1 byte length
    LIST_WITH_LENGTH2 = 0x72  # 2 byte length
    OPTIONAL = 0x01  # within lists
    SEQUENCE = 0x77


class SMLSignatureMode(IntEnum):
    """SML cryptographic signature modes."""
    NONE = 0
    AES_CMAC = 1
    RSA_SHA256 = 2
    ECDSA_P256 = 3
