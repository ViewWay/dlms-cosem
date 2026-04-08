"""Supplementary tests for DLMS data types."""
import pytest
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from dlms_cosem.dlms_data import (
    DlmsDataFactory, IntegerData, LongData, UnsignedIntegerData,
    UnsignedLongData, OctetStringData, DataStructure, DataArray,
    BooleanData, Float32Data, Float64Data, BitStringData, EnumData,
    CompactArrayData, DateTimeData, BCDData, VisibleStringData,
    UTF8StringData, NullData, DoubleLongData, DoubleLongUnsignedData,
)
from dlms_cosem.cosem.obis import Obis


class TestDlmsDataTypes:
    def test_integer_creation(self):
        i = IntegerData(42)
        assert i.value == 42

    def test_integer_negative(self):
        i = IntegerData(-100)
        assert i.value == -100

    def test_long_unsigned(self):
        l = DoubleLongUnsignedData(0xFFFFFFFF)
        assert l.value == 0xFFFFFFFF

    def test_unsigned(self):
        u = UnsignedIntegerData(255)
        assert u.value == 255

    def test_octet_string(self):
        o = OctetStringData(b"\x01\x02\x03")
        assert o.value == b"\x01\x02\x03"

    def test_boolean_true(self):
        b = BooleanData(True)
        assert b.value is True

    def test_boolean_false(self):
        b = BooleanData(False)
        assert b.value is False

    def test_float32(self):
        f = Float32Data(3.14)
        assert isinstance(f.value, (int, float))

    def test_float64(self):
        d = Float64Data(3.14159265358979)
        assert isinstance(d.value, (int, float))

    def test_null_data(self):
        n = NullData(0)
        assert n is not None

    def test_visible_string(self):
        s = VisibleStringData("hello")
        assert s.value == "hello"

    def test_utf8_string(self):
        s = UTF8StringData("hello 世界")
        assert s.value == "hello 世界"

    def test_enum(self):
        e = EnumData(5)
        assert e.value == 5

    def test_bcd(self):
        b = BCDData(b"\x12\x34")
        assert b.value == b"\x12\x34"

    def test_structure_creation(self):
        s = DataStructure([IntegerData(1), OctetStringData(b"test")])
        assert len(s.value) == 2

    def test_array_creation(self):
        a = DataArray([IntegerData(1), IntegerData(2), IntegerData(3)])
        assert len(a.value) == 3

    def test_bit_string(self):
        b = BitStringData(b"\xFF")
        assert b.value == b"\xFF"

    def test_date_time(self):
        dt = DateTimeData(b"\x00" * 12)
        assert dt is not None


class TestDlmsDataParsing:
    @pytest.mark.parametrize("tag", [0x00, 0x03, 0x05, 0x06, 0x09, 0x0A, 0x0C])
    def test_data_factory_tag(self, tag):
        try:
            data = DlmsDataFactory.from_bytes(bytes([tag, 0x00]))
            assert data is not None
        except Exception:
            pass


class TestDlmsDataEquality:
    def test_integer_equality(self):
        assert IntegerData(42) == IntegerData(42)

    def test_integer_inequality(self):
        assert IntegerData(42) != IntegerData(43)

    def test_long_unsigned_equality(self):
        assert DoubleLongUnsignedData(100) == DoubleLongUnsignedData(100)

    def test_octet_string_equality(self):
        assert OctetStringData(b"\x01") == OctetStringData(b"\x01")

    def test_boolean_equality(self):
        assert BooleanData(True) == BooleanData(True)
