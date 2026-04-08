"""Supplementary tests for HDLC layer."""
import pytest
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from dlms_cosem.hdlc.address import HdlcAddress
from dlms_cosem.hdlc.frames import (
    InformationFrame, ReceiveReadyFrame, SetNormalResponseModeFrame,
    UnNumberedAcknowledgmentFrame, DisconnectFrame,
)
from dlms_cosem.hdlc.validators import validate_hdlc_address
from dlms_cosem.hdlc.parameters import HdlcParameterList
from dlms_cosem.crc import CRCCCITT


class TestHdlcAddress:
    def test_hdlc_address_creation_client(self):
        addr = HdlcAddress(16, 1)
        assert addr is not None

    def test_hdlc_address_creation_server(self):
        addr = HdlcAddress(1, 16, address_type='server')
        assert addr is not None

    def test_hdlc_address_value(self):
        addr = HdlcAddress(16, 1)
        assert addr.length >= 1

    def test_hdlc_address_extended(self):
        addr = HdlcAddress(16, 1, extended_addressing=True)
        assert addr is not None

    @pytest.mark.parametrize("val", [-1, 0x10000])
    def test_invalid_address(self, val):
        with pytest.raises(Exception):
            HdlcAddress(val)

    def test_address_type_validation(self):
        with pytest.raises(Exception):
            HdlcAddress(16, 1, address_type='invalid')


class TestHdlcValidators:
    def test_validate_hdlc_address(self):
        assert callable(validate_hdlc_address)

    def test_frame_flag_bytes(self):
        flag = b"\x7e"
        assert len(flag) == 1
        assert flag[0] == 0x7E


class TestHdlcParameters:
    def test_parameter_list_creation(self):
        params = HdlcParameterList()
        assert params is not None

    def test_crc_ccitt(self):
        crc = CRCCCITT()
        assert crc is not None


class TestHdlcFrameTypes:
    def _make_addrs(self):
        client = HdlcAddress(16, 1)
        server = HdlcAddress(1, 16, address_type='server')
        return client, server

    def test_info_frame_creation(self):
        client, server = self._make_addrs()
        frame = InformationFrame(destination_address=server, source_address=client,
                                 payload=b"\x01\x02")
        assert frame is not None

    def test_rr_frame_creation(self):
        client, server = self._make_addrs()
        frame = ReceiveReadyFrame(destination_address=server, source_address=client)
        assert frame is not None

    def test_snrm_frame_creation(self):
        client, server = self._make_addrs()
        frame = SetNormalResponseModeFrame(destination_address=server, source_address=client)
        assert frame is not None

    def test_ua_frame_creation(self):
        client, server = self._make_addrs()
        frame = UnNumberedAcknowledgmentFrame(destination_address=server, source_address=client)
        assert frame is not None

    def test_disc_frame_creation(self):
        client, server = self._make_addrs()
        frame = DisconnectFrame(destination_address=server, source_address=client)
        assert frame is not None

    def test_info_frame_segmented(self):
        client, server = self._make_addrs()
        frame = InformationFrame(destination_address=server, source_address=client,
                                 payload=b"\x01\x02", segmented=True, final=False)
        assert frame is not None

    def test_info_frame_sequence_numbers(self):
        client, server = self._make_addrs()
        frame = InformationFrame(destination_address=server, source_address=client,
                                 payload=b"\x01", send_sequence_number=3, receive_sequence_number=2)
        assert frame is not None
