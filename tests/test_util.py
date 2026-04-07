"""Tests for dlms_cosem.util module — DataConversion, Log, Singleton."""

import threading
import time
import pytest


# ─── DataConversion ────────────────────────────────────────────────

class TestDataConversion:
    """Test DataConversion static methods."""

    @pytest.fixture
    def dc(self):
        from dlms_cosem.util.data_conversion import DataConversion
        return DataConversion

    # hex_to_dec
    def test_hex_to_dec_unsigned(self, dc):
        assert dc.hex_to_dec("0A") == 10
        assert dc.hex_to_dec("FF") == 255

    def test_hex_to_dec_empty(self, dc):
        assert dc.hex_to_dec("") == 0

    def test_hex_to_dec_signed(self, dc):
        result = dc.hex_to_dec("FF", "Integer")
        assert result < 0  # Two's complement negative

    # dec_to_hex_str
    def test_dec_to_hex_basic(self, dc):
        assert dc.dec_to_hex_str(10) == "0A"
        assert dc.dec_to_hex_str(255) == "FF"

    def test_dec_to_hex_negative(self, dc):
        result = dc.dec_to_hex_str(-1)
        assert isinstance(result, str)
        assert len(result) > 0

    def test_dec_to_hex_padded(self, dc):
        result = dc.dec_to_hex_str(10, length=4)
        assert result == "000A"

    # obis_to_hex / hex_to_obis
    def test_obis_roundtrip(self, dc):
        obis = "1-0:96.1.0.255"
        hex_val = dc.obis_to_hex(obis)
        assert dc.hex_to_obis(hex_val) == obis

    def test_obis_empty(self, dc):
        assert dc.obis_to_hex("") == ""

    def test_hex_to_obis_invalid(self, dc):
        assert dc.hex_to_obis("not_valid") == "not_valid"

    # ascii_to_hex / hex_to_ascii
    def test_ascii_roundtrip(self, dc):
        s = "Hello"
        assert dc.hex_to_ascii(dc.ascii_to_hex(s)) == s

    def test_ascii_to_hex_known(self, dc):
        assert dc.ascii_to_hex("A") == "41"
        assert dc.ascii_to_hex("AB") == "4142"

    # bytes_to_hex_str / hex_str_to_bytes
    def test_bytes_roundtrip(self, dc):
        data = bytes([0x01, 0x02, 0x03])
        assert dc.hex_str_to_bytes(dc.bytes_to_hex_str(data)) == data

    def test_bytes_to_hex_format(self, dc):
        assert dc.bytes_to_hex_str(b"\x01\xFF") == "01 FF"

    # BCD
    def test_bcd_roundtrip(self, dc):
        for val in [0, 42, 99, 255, 9999]:
            assert dc.bcd_to_dec(dc.dec_to_bcd(val)) == val

    def test_bcd_invalid(self, dc):
        with pytest.raises(ValueError):
            dc.dec_to_bcd(-1)
        with pytest.raises(ValueError):
            dc.dec_to_bcd(10000)

    # reverse_bytes
    def test_reverse_bytes(self, dc):
        assert dc.reverse_bytes(b"\x01\x02\x03") == b"\x03\x02\x01"

    # split_with_space
    def test_split_with_space(self, dc):
        assert dc.split_with_space("0102FF") == "01 02 FF"
        assert dc.split_with_space("01 02") == "01 02"


# ─── Log ────────────────────────────────────────────────────────────

class TestLog:
    """Test Log utility."""

    def test_log_import(self):
        from dlms_cosem.util.log import Log
        assert Log is not None

    def test_log_constants(self):
        from dlms_cosem.util.log import LogConstant
        assert hasattr(LogConstant, 'LOG_DIR')
        assert hasattr(LogConstant, 'MAX_LOG_SIZE_BYTES')
        assert LogConstant.MAX_LOG_SIZE_BYTES == 1024 * 1024 * 20


# ─── Singleton ──────────────────────────────────────────────────────

class TestSingleton:
    """Test thread-safe Singleton metaclass."""

    def test_singleton_attributes(self):
        from dlms_cosem.util.singleton import Singleton
        s1 = Singleton()
        s2 = Singleton()
        # Singleton is a plain class (not a metaclass)
        assert hasattr(Singleton, 'CONN')
        assert hasattr(Singleton, 'ObisDataType')
        assert hasattr(Singleton, '_instance_lock')

    def test_singleton_global_state(self):
        from dlms_cosem.util.singleton import Singleton
        Singleton.MeterNo = "TEST001"
        assert Singleton.MeterNo == "TEST001"
        Singleton.MeterNo = ""  # cleanup
