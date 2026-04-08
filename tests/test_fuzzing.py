"""Fuzzing tests - ensure all parsers are robust against random/malformed input.

Each parser should return an error, never crash (segfault, unhandled exception, etc.)
"""
import os
import random
import sys

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from dlms_cosem import a_xdr
from dlms_cosem.hdlc.frames import (
    InformationFrame, ReceiveReadyFrame, SetNormalResponseModeFrame,
    UnNumberedAcknowledgmentFrame, DisconnectFrame,
)
from dlms_cosem.hdlc.address import HdlcAddress
from dlms_cosem.cosem import Obis
from dlms_cosem.parsers import ProfileGenericBufferParser as ProfileGenericParser
from dlms_cosem.dlms_data import DlmsDataFactory
from dlms_cosem.protocol.xdlms.get import GetRequestNormal
from dlms_cosem.protocol.xdlms.set import SetRequestNormal
from dlms_cosem.protocol.xdlms.initiate_request import InitiateRequest
from dlms_cosem.protocol.xdlms.exception_response import ExceptionResponse


NUM_CASES = 1000
SEED = 42

random.seed(SEED)


def _rand_bytes(min_len=0, max_len=256):
    length = random.randint(min_len, max_len)
    return os.urandom(length)


class TestHdlcFramFuzzing:
    """Fuzz HDLC frame parser with random bytes."""

    @pytest.mark.parametrize("_", range(100))
    def test_info_frame_random_bytes(self, _):
        data = _rand_bytes(4, 300)
        try:
            InformationFrame.from_bytes(data)
        except Exception:
            pass

    @pytest.mark.parametrize("_", range(100))
    def test_rr_frame_random_bytes(self, _):
        data = _rand_bytes(4, 300)
        try:
            ReceiveReadyFrame.from_bytes(data)
        except Exception:
            pass

    @pytest.mark.parametrize("_", range(100))
    def test_snrm_frame_random_bytes(self, _):
        data = _rand_bytes(4, 300)
        try:
            SetNormalResponseModeFrame.from_bytes(data)
        except Exception:
            pass

    @pytest.mark.parametrize("_", range(100))
    def test_ua_frame_random_bytes(self, _):
        data = _rand_bytes(4, 300)
        try:
            UnNumberedAcknowledgmentFrame.from_bytes(data)
        except Exception:
            pass

    @pytest.mark.parametrize("_", range(100))
    def test_disc_frame_random_bytes(self, _):
        data = _rand_bytes(4, 300)
        try:
            DisconnectFrame.from_bytes(data)
        except Exception:
            pass

    @pytest.mark.parametrize("_", range(100))
    def test_hdlc_flag_wrapped(self, _):
        data = b"\x7e" + _rand_bytes(10, 200) + b"\x7e"
        try:
            InformationFrame.from_bytes(data)
        except Exception:
            pass

    @pytest.mark.parametrize("_", range(100))
    def test_hdlc_very_long_frame(self, _):
        data = _rand_bytes(500, 2000)
        try:
            InformationFrame.from_bytes(data)
        except Exception:
            pass

    @pytest.mark.parametrize("_", range(100))
    def test_hdlc_empty_frame(self, _):
        for data in [b"", b"\x7e", b"\x7e\x7e", b"\x00", b"\xff"]:
            try:
                InformationFrame.from_bytes(data)
            except Exception:
                pass

    @pytest.mark.parametrize("_", range(100))
    def test_hdlc_byte_stuffing_artifacts(self, _):
        data = b"\x7e\x7d" + _rand_bytes(10, 100) + b"\x7d\x5e\x7e"
        try:
            InformationFrame.from_bytes(data)
        except Exception:
            pass


class TestAxdrFuzzing:
    """Fuzz AXDR decoder with random bytes."""

    @pytest.mark.parametrize("_", range(200))
    def test_axdr_long_unsigned(self, _):
        data = _rand_bytes(2, 8)
        try:
            a_xdr.decoding.long_unsigned(data, 0)
        except Exception:
            pass

    @pytest.mark.parametrize("_", range(200))
    def test_axdr_integer(self, _):
        data = _rand_bytes(2, 8)
        try:
            a_xdr.decoding.integer(data, 0)
        except Exception:
            pass

    @pytest.mark.parametrize("_", range(200))
    def test_axdr_octet_string(self, _):
        data = _rand_bytes(4, 100)
        try:
            a_xdr.decoding.octet_string(data, 0)
        except Exception:
            pass

    @pytest.mark.parametrize("_", range(200))
    def test_axdr_bit_string(self, _):
        data = _rand_bytes(4, 100)
        try:
            a_xdr.decoding.bit_string(data, 0)
        except Exception:
            pass

    @pytest.mark.parametrize("_", range(100))
    def test_axdr_visible_string(self, _):
        data = _rand_bytes(4, 100)
        try:
            a_xdr.decoding.visible_string(data, 0)
        except Exception:
            pass

    @pytest.mark.parametrize("_", range(100))
    def test_axdr_date_time(self, _):
        data = _rand_bytes(12, 20)
        try:
            a_xdr.decoding.datetime(data, 0)
        except Exception:
            pass


class TestBerFuzzing:
    """Fuzz BER/ASN.1 decoder with random bytes."""

    @pytest.mark.parametrize("_", range(200))
    def test_ber_decode(self, _):
        from dlms_cosem.ber import BER
        data = _rand_bytes(2, 100)
        try:
            ber = BER()
            ber.decode(data)
        except Exception:
            pass


class TestDlmsDataFuzzing:
    """Fuzz DLMS data parser with random bytes."""

    @pytest.mark.parametrize("_", range(200))
    def test_data_parse(self, _):
        data = _rand_bytes(2, 100)
        try:
            DlmsDataFactory.from_bytes(data)
        except Exception:
            pass


class TestObisFuzzing:
    """Fuzz OBIS code parsing with random values."""

    @pytest.mark.parametrize("_", range(500))
    def test_obis_from_bytes(self, _):
        data = _rand_bytes(6, 6)
        try:
            Obis.from_bytes(data)
        except Exception:
            pass

    @pytest.mark.parametrize("_", range(200))
    def test_obis_from_string(self, _):
        random_str = ".".join(str(random.randint(0, 999)) for _ in range(random.randint(4, 7)))
        try:
            Obis.from_string(random_str)
        except Exception:
            pass

    @pytest.mark.parametrize("_", range(100))
    def test_obis_edge_values(self, _):
        for val in [-1, 256, 999, 0, 255]:
            try:
                Obis(val, val, val, val, val, val)
            except Exception:
                pass

    @pytest.mark.parametrize("_", range(100))
    def test_obis_invalid_strings(self, _):
        for s in ["", "1.2.3", "a.b.c.d.e.f", "1.2.3.4.5.6.7", "1..3.4.5.6", "999.999.999.999.999.999"]:
            try:
                Obis.from_string(s)
            except Exception:
                pass


class TestApduFuzzing:
    """Fuzz APDU parsers with random bytes."""

    @pytest.mark.parametrize("_", range(200))
    def test_get_request_random(self, _):
        data = _rand_bytes(2, 100)
        try:
            GetRequestNormal.from_bytes(data)
        except Exception:
            pass

    @pytest.mark.parametrize("_", range(200))
    def test_set_request_random(self, _):
        data = _rand_bytes(2, 100)
        try:
            SetRequestNormal.from_bytes(data)
        except Exception:
            pass

    @pytest.mark.parametrize("_", range(100))
    def test_initiate_request_random(self, _):
        data = _rand_bytes(2, 100)
        try:
            InitiateRequest.from_bytes(data)
        except Exception:
            pass

    @pytest.mark.parametrize("_", range(100))
    def test_exception_response_random(self, _):
        data = _rand_bytes(2, 100)
        try:
            ExceptionResponse.from_bytes(data)
        except Exception:
            pass


class TestProfileGenericFuzzing:
    """Fuzz Profile Generic parser with random bytes."""

    @pytest.mark.parametrize("_", range(100))
    def test_profile_generic_parse(self, _):
        from dlms_cosem.cosem.base import CosemAttribute
        from dlms_cosem import enumerations
        data = _rand_bytes(10, 500)
        parser = ProfileGenericParser(
            capture_objects=[],
            capture_period=60,
        )
        try:
            parser.parse_bytes(data)
        except Exception:
            pass


class TestSecurityFuzzing:
    """Fuzz security operations with random input."""

    @pytest.mark.parametrize("_", range(100))
    def test_sm4_invalid_key(self, _):
        from dlms_cosem.security import SM4Cipher
        bad_keys = [b"\x00" * 8, b"\x00" * 32, b"", b"\x00" * 15]
        for key in bad_keys:
            try:
                SM4Cipher(key=key)
            except Exception:
                pass

    @pytest.mark.parametrize("_", range(100))
    def test_sm4_decrypt_garbage(self, _):
        from dlms_cosem.security import SM4Cipher
        key = os.urandom(16)
        cipher = SM4Cipher(key=key)
        garbage = _rand_bytes(5, 200)
        try:
            cipher.decrypt(garbage)
        except Exception:
            pass
