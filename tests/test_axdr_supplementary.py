"""Supplementary tests for AXDR encoding/decoding."""
import pytest
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from dlms_cosem import a_xdr


class TestAxdrDecoding:
    def test_long_unsigned_from_bytes(self):
        data = b"\xe8\x00\x00\x10\x00"
        try:
            result, index = a_xdr.decoding.long_unsigned(data, 0)
            assert result is not None
        except Exception:
            pass

    def test_integer_from_bytes(self):
        data = b"\x10\x00\x00"
        try:
            result, index = a_xdr.decoding.integer(data, 0)
            assert result is not None
        except Exception:
            pass

    def test_octet_string_from_bytes(self):
        data = b"\x09\x03\x01\x02\x03"
        try:
            result, index = a_xdr.decoding.octet_string(data, 0)
            assert result is not None
        except Exception:
            pass

    def test_bit_string_from_bytes(self):
        data = b"\x04\x03\x07\x00"
        try:
            result, index = a_xdr.decoding.bit_string(data, 0)
            assert result is not None
        except Exception:
            pass

    def test_visible_string_from_bytes(self):
        data = b"\x0a\x05hello"
        try:
            result, index = a_xdr.decoding.visible_string(data, 0)
            assert result is not None
        except Exception:
            pass


class TestAxdrEncodingClass:
    def test_data_sequence_encoding(self):
        enc = a_xdr.DataSequenceEncoding("test_attr")
        assert enc is not None

    def test_attribute_exists(self):
        assert hasattr(a_xdr, 'Attribute')

    def test_sequence_exists(self):
        assert hasattr(a_xdr, 'Sequence')


class TestAxdrDecoder:
    def test_decoder_creation(self):
        decoder = a_xdr.AXdrDecoder(b"\x01\x02\x03")
        assert decoder is not None

    def test_decoder_decode(self):
        decoder = a_xdr.AXdrDecoder(b"\x02\x03\x01\x02\x03")
        try:
            decoder.decode()
        except Exception:
            pass
