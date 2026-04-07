"""Data conversion utilities for DLMS/COSEM.

This module provides data conversion functions for hex/decimal/OBIS/ASCII
operations, compatible with DLMS/COSEM requirements.

Reference: pdlms/pdlms/util/data_conversion.py
"""

import re
from typing import Union


class DataConversion:
    """
    Data conversion utilities for DLMS/COSEM.

    Provides static methods for converting between different data formats
    commonly used in DLMS/COSEM protocol implementation.
    """

    @staticmethod
    def hex_to_dec(hex_str: str, data_type: str | None = None) -> int:
        """
        Convert hexadecimal string to decimal integer.

        Args:
            hex_str: Hexadecimal string (e.g., "0A", "FF")
            data_type: Data type for signed/unsigned handling

        Returns:
            Decimal integer value
        """
        if data_type is None or "Unsigned" in str(data_type) or data_type == "Enum":
            if len(str(hex_str).strip()) > 0:
                return int(str(hex_str), 16)
            return 0
        num = int(str(hex_str), 16)
        # Handle signed numbers (two's complement)
        if int(str(hex_str)[0], 16) >> 3:
            num -= int("F" * len(str(hex_str)), 16) + 1
        return num

    @staticmethod
    def dec_to_hex_str(dec: int, length: int = 0, data_type: str | None = None) -> str:
        """
        Convert decimal integer to hexadecimal string.

        Args:
            dec: Decimal integer
            length: Fixed length (zero-padded)
            data_type: Data type for signed/unsigned handling

        Returns:
            Hexadecimal string (uppercase)
        """
        dec = int(dec)
        if dec < 0:
            # Two's complement for negative numbers
            origin_code = bin(abs(dec))[2:].rjust(64, "0")
            inverse_code = "1" + "".join("0" if e == "1" else "1" for e in origin_code[1:])
            complement_code = int(inverse_code, 2) + 1
            if length == 0:
                return hex(complement_code & ((1 << 64) - 1))[2:].upper()
            return hex(complement_code & ((1 << 64) - 1))[2:].upper()[-length:]

        if length == 0:
            response = hex(dec)[2:].upper()
            if len(response) in (1, 3, 5, 7):
                return "0" + response
            return response
        return hex(dec)[2:].rjust(length, "0").upper()

    @staticmethod
    def obis_to_hex(obis: str) -> str:
        """
        Convert OBIS code string to hex string.

        Args:
            obis: OBIS code string (e.g., "1-0:96.1.0.255")

        Returns:
            Hexadecimal string representation (12 bytes)
        """
        if obis == "":
            return ""
        if not re.search(r"[\.,\-,\:]", obis):
            return obis
        lst = re.split(r"[\.,\-,\:]", obis)
        if len([item for item in lst if int(item) > 255 or int(item) < 0]) == 0:
            return "".join(["{:02x}".format(int(item)) for item in lst]).upper()
        return obis

    @staticmethod
    def hex_to_obis(hex_obis: str) -> str:
        """
        Convert hex string to OBIS code string.

        Args:
            hex_obis: Hexadecimal string (12 bytes)

        Returns:
            OBIS code string (e.g., "1-0:96.1.0.255")
        """
        if re.match(r"^[0-9a-fA-F]{12}$", hex_obis):
            lst = re.findall(r"([0-9a-fA-F]{2})", hex_obis)
            result = str(int(lst[0], 16)) + "-" + str(int(lst[1], 16)) + ":"
            for item in lst[2:]:
                result += str(int(item, 16)) + "."
            return result.strip(".")
        return hex_obis

    @staticmethod
    def ascii_to_hex(s: str) -> str:
        """
        Convert ASCII string to hexadecimal string.

        Args:
            s: ASCII string

        Returns:
            Hexadecimal string (uppercase)
        """
        return "".join(hex(ord(c))[2:].rjust(2, "0") for c in str(s)).upper()

    @staticmethod
    def hex_to_ascii(hex_str: str) -> str:
        """
        Convert hexadecimal string to ASCII string.

        Args:
            hex_str: Hexadecimal string

        Returns:
            ASCII string
        """
        return "".join(chr(int(hex_str[i : i + 2], 16)) for i in range(0, len(hex_str), 2))

    @staticmethod
    def bytes_to_hex_str(data: bytes) -> str:
        """
        Convert bytes to hexadecimal string with space separator.

        Args:
            data: Bytes data

        Returns:
            Hexadecimal string with space separator (e.g., "01 02 03")
        """
        return " ".join(f"{b:02X}" for b in data)

    @staticmethod
    def hex_str_to_bytes(hex_str: str) -> bytes:
        """
        Convert hexadecimal string to bytes.

        Args:
            hex_str: Hexadecimal string (with or without spaces)

        Returns:
            Bytes data
        """
        # Remove spaces and separators
        cleaned = hex_str.replace(" ", "").replace("-", "").replace(":", "")
        return bytes.fromhex(cleaned)

    @staticmethod
    def dec_to_bcd(dec: int) -> bytes:
        """
        Convert decimal integer to BCD (Binary Coded Decimal).

        Args:
            dec: Decimal integer (0-99)

        Returns:
            BCD bytes (1 byte for 0-99, 2 bytes for 100-9999)
        """
        dec = int(dec)
        if dec < 0 or dec > 9999:
            raise ValueError(f"Decimal must be 0-9999, got {dec}")

        hex_str = f"{dec:04d}"
        bcd = 0
        for digit in hex_str:
            bcd = (bcd << 4) | int(digit)

        return bcd.to_bytes(2, byteorder='big')

    @staticmethod
    def bcd_to_dec(bcd: bytes) -> int:
        """
        Convert BCD (Binary Coded Decimal) to decimal integer.

        Args:
            bcd: BCD bytes

        Returns:
            Decimal integer
        """
        dec_str = ""
        for byte in bcd:
            dec_str += f"{byte >> 4:01d}{byte & 0x0F:01d}"
        return int(dec_str)

    @staticmethod
    def reverse_bytes(data: bytes) -> bytes:
        """
        Reverse byte order of byte array.

        Args:
            data: Input bytes

        Returns:
            Reversed bytes
        """
        return data[::-1]

    @staticmethod
    def split_with_space(hex_str: str) -> str:
        """
        Split hexadecimal string with space every 2 characters.

        Args:
            hex_str: Hexadecimal string

        Returns:
            Space-separated hex string
        """
        cleaned = hex_str.replace(" ", "")
        return " ".join([cleaned[i:i+2] for i in range(0, len(cleaned), 2)])
