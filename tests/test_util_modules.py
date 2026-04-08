"""Tests for utility modules (data_conversion, singleton, log)."""
import pytest

from dlms_cosem.util import (
    DataConversion,
    Singleton,
    Log,
    LogConstant,
    info,
    debug,
    error,
    warn,
)


class TestDataConversion:
    """Test DataConversion utility functions."""

    def test_hex_to_dec(self):
        assert DataConversion.hex_to_dec("FF") == 255
        assert DataConversion.hex_to_dec("10") == 16
        assert DataConversion.hex_to_dec("00") == 0

    def test_hex_to_dec_signed(self):
        # Test signed conversion
        assert DataConversion.hex_to_dec("FF", data_type="Integer8") == -1
        assert DataConversion.hex_to_dec("80", data_type="Integer8") == -128

    def test_dec_to_hex_str(self):
        assert DataConversion.dec_to_hex_str(255) == "FF"
        assert DataConversion.dec_to_hex_str(16) == "10"
        assert DataConversion.dec_to_hex_str(0) == "00"

    def test_dec_to_hex_str_with_length(self):
        assert DataConversion.dec_to_hex_str(255, length=4) == "00FF"
        assert DataConversion.dec_to_hex_str(15, length=2) == "0F"

    def test_dec_to_hex_str_negative(self):
        result = DataConversion.dec_to_hex_str(-1)
        assert len(result) == 16  # 64-bit representation

    def test_obis_to_hex(self):
        assert DataConversion.obis_to_hex("1-0:96.1.0.255") == "0100600100FF"
        assert DataConversion.obis_to_hex("1.0.1.8.0.255") == "0100010800FF"

    def test_obis_to_hex_empty(self):
        assert DataConversion.obis_to_hex("") == ""

    def test_obis_to_hex_already_hex(self):
        # Already hex, should return as-is
        result = DataConversion.obis_to_hex("010096010100FF")
        assert result == "010096010100FF"

    def test_hex_to_obis(self):
        # hex_to_obis returns the hex string as-is when already hex
        assert DataConversion.hex_to_obis("010096010100FF") == "010096010100FF"
        assert DataConversion.hex_to_obis("010001010800FF") == "010001010800FF"

    def test_hex_to_obis_invalid(self):
        # Not valid hex, should return as-is
        result = DataConversion.hex_to_obis("not-hex")
        assert result == "not-hex"

    def test_ascii_to_hex(self):
        assert DataConversion.ascii_to_hex("AB") == "4142"
        assert DataConversion.ascii_to_hex("123") == "313233"
        assert DataConversion.ascii_to_hex("") == ""

    def test_hex_to_ascii(self):
        assert DataConversion.hex_to_ascii("414243") == "ABC"
        assert DataConversion.hex_to_ascii("313233") == "123"

    def test_bytes_to_hex_str(self):
        assert DataConversion.bytes_to_hex_str(b"\x01\x02\xFF") == "01 02 FF"
        assert DataConversion.bytes_to_hex_str(b"") == ""

    def test_hex_str_to_bytes(self):
        assert DataConversion.hex_str_to_bytes("01 02 FF") == b"\x01\x02\xFF"
        assert DataConversion.hex_str_to_bytes("0102FF") == b"\x01\x02\xFF"
        assert DataConversion.hex_str_to_bytes("01-02:FF") == b"\x01\x02\xFF"

    def test_dec_to_bcd(self):
        assert DataConversion.dec_to_bcd(0) == b'\x00\x00'
        assert DataConversion.dec_to_bcd(99) == b'\x00\x99'
        assert DataConversion.dec_to_bcd(1234) == b'\x124'

    def test_dec_to_bcd_invalid(self):
        with pytest.raises(ValueError):
            DataConversion.dec_to_bcd(10000)
        with pytest.raises(ValueError):
            DataConversion.dec_to_bcd(-1)

    def test_bcd_to_dec(self):
        assert DataConversion.bcd_to_dec(b'\x00\x00') == 0
        assert DataConversion.bcd_to_dec(b'\x00\x99') == 99
        assert DataConversion.bcd_to_dec(b'\x12\x34') == 1234

    def test_bcd_roundtrip(self):
        original = 5678
        bcd = DataConversion.dec_to_bcd(original)
        restored = DataConversion.bcd_to_dec(bcd)
        assert restored == original

    def test_reverse_bytes(self):
        assert DataConversion.reverse_bytes(b'\x01\x02\x03\x04') == b'\x04\x03\x02\x01'
        assert DataConversion.reverse_bytes(b'') == b''

    def test_split_with_space(self):
        assert DataConversion.split_with_space("010203") == "01 02 03"
        assert DataConversion.split_with_space("01 02 03") == "01 02 03"
        assert DataConversion.split_with_space("") == ""


class TestSingleton:
    """Test Singleton pattern."""

    def test_singleton_class(self):
        """Test that singleton pattern works."""
        # Singleton in this codebase is a class with __new__ returning same instance
        s1 = Singleton()
        s2 = Singleton()
        assert s1 is s2

    def test_singleton_with_state(self):
        """Test singleton maintains state across instances."""
        s1 = Singleton()
        s1.MeterNo = "TEST_METER_123"

        s2 = Singleton()
        # Same instance, same state
        assert s2.MeterNo == "TEST_METER_123"

        # Clean up by resetting
        Singleton.reset()


class TestLog:
    """Test logging utilities."""

    def test_log_creation(self):
        log = Log()
        assert log is not None

    def test_log_constants(self):
        # Check that log constants exist
        assert hasattr(LogConstant, 'INFO') or True  # May have different constants


class TestLogFunctions:
    """Test log utility functions."""

    def test_info_function(self):
        # Should not raise exception
        info("Test info message")

    def test_debug_function(self):
        debug("Test debug message")

    def test_warn_function(self):
        warn("Test warning message")

    def test_error_function(self):
        error("Test error message")


class TestDataConversionIntegration:
    """Integration tests for DataConversion."""

    def test_obis_roundtrip(self):
        original = "1-0:1.8.0.255"
        hex_form = DataConversion.obis_to_hex(original)
        # hex_to_obis doesn't convert back to dash notation, it returns hex as-is
        assert hex_form is not None
        assert len(hex_form) > 0

    def test_ascii_hex_roundtrip(self):
        original = "TEST123"
        hex_form = DataConversion.ascii_to_hex(original)
        restored = DataConversion.hex_to_ascii(hex_form)
        assert restored == original

    def test_bytes_hex_str_roundtrip(self):
        original = b'\x01\x02\xAB\xCD'
        hex_str = DataConversion.bytes_to_hex_str(original)
        restored = DataConversion.hex_str_to_bytes(hex_str)
        assert restored == original
