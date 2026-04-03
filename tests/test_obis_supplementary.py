"""Supplementary tests for OBIS codes."""
import pytest
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from dlms_cosem.cosem.obis import Obis


class TestObisCreation:
    def test_basic_creation(self):
        obis = Obis(0, 0, 1, 0, 0, 255)
        assert obis.a == 0
        assert obis.b == 0
        assert obis.c == 1
        assert obis.d == 0
        assert obis.e == 0
        assert obis.f == 255

    @pytest.mark.parametrize("a,b,c,d,e,f", [
        (0, 0, 1, 0, 0, 255),
        (0, 0, 2, 0, 0, 255),
        (1, 0, 1, 8, 0, 255),
        (1, 0, 1, 8, 1, 255),
        (1, 0, 1, 8, 2, 255),
        (0, 0, 96, 10, 0, 255),
        (0, 0, 96, 1, 0, 255),
        (0, 0, 0, 0, 0, 255),
    ])
    def test_common_obis(self, a, b, c, d, e, f):
        obis = Obis(a, b, c, d, e, f)
        assert (obis.a, obis.b, obis.c, obis.d, obis.e, obis.f) == (a, b, c, d, e, f)

    @pytest.mark.parametrize("a,b,c,d,e,f", [
        (255, 255, 255, 255, 255, 255),
        (0, 0, 0, 0, 0, 0),
        (128, 128, 128, 128, 128, 128),
    ])
    def test_boundary_values(self, a, b, c, d, e, f):
        obis = Obis(a, b, c, d, e, f)
        assert obis.a == a


class TestObisString:
    def test_from_string_standard(self):
        obis = Obis.from_string("0.0.1.0.0.255")
        assert (obis.a, obis.b, obis.c, obis.d, obis.e, obis.f) == (0, 0, 1, 0, 0, 255)

    def test_str_representation(self):
        obis = Obis(0, 0, 1, 0, 0, 255)
        s = str(obis)
        assert "0" in s

    def test_equality(self):
        o1 = Obis(0, 0, 1, 0, 0, 255)
        o2 = Obis(0, 0, 1, 0, 0, 255)
        assert o1 == o2

    def test_inequality(self):
        o1 = Obis(0, 0, 1, 0, 0, 255)
        o2 = Obis(0, 0, 2, 0, 0, 255)
        assert o1 != o2

    def test_from_string_invalid(self):
        for s in ["", "1.2.3", "a.b.c.d.e.f"]:
            with pytest.raises(Exception):
                Obis.from_string(s)


class TestObisBytes:
    def test_to_bytes_length(self):
        obis = Obis(0, 0, 1, 0, 0, 255)
        data = obis.to_bytes()
        assert len(data) == 6

    def test_from_bytes_roundtrip(self):
        original = Obis(0, 0, 1, 0, 0, 255)
        data = original.to_bytes()
        restored = Obis.from_bytes(data)
        assert original == restored

    @pytest.mark.parametrize("a,b,c,d,e,f", [
        (0, 0, 1, 0, 0, 255),
        (1, 0, 1, 8, 0, 255),
        (255, 255, 255, 255, 255, 255),
        (0, 0, 0, 0, 0, 0),
    ])
    def test_roundtrip_all(self, a, b, c, d, e, f):
        obis = Obis(a, b, c, d, e, f)
        assert Obis.from_bytes(obis.to_bytes()) == obis
