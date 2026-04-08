"""Tests for SML (Smart Message Language) parser."""
import pytest

from dlms_cosem.sml import (
    SMLParser, SMLTag, SMLType, SMLPublicKey, SMLValueEntry,
    SMLFile, SMLMessage, SMLSignatureMode, SMLToDLMSBridge,
)


class TestSMLPublicKey:
    def test_fingerprint(self):
        key = SMLPublicKey(key_value=b"test key data")
        assert len(key.fingerprint) == 64  # SHA256 hex

    def test_verify_none(self):
        key = SMLPublicKey(signature_mode=SMLSignatureMode.NONE)
        assert key.verify(b"data", b"sig")


class TestSMLValueEntry:
    def test_obis_str(self):
        entry = SMLValueEntry(obis=b"\x01\x00\x01\x08\x00\xff", value=12345)
        assert entry.obis_str == "1.0.1.8.0.255"


class TestSMLParser:
    def test_parse_empty(self):
        parser = SMLParser()
        result = parser.parse(b"")
        assert isinstance(result, SMLFile)
        assert len(result.messages) == 0

    def test_parse_end_of_file(self):
        parser = SMLParser()
        data = b"\x1b\x1b\x1b\x1b"
        result = parser.parse(data)
        assert isinstance(result, SMLFile)

    def test_parse_incomplete(self):
        parser = SMLParser()
        data = b"\x01"  # GET_OPEN_REQUEST tag but nothing else
        result = parser.parse(data)
        # Should not crash, might have empty messages
        assert isinstance(result, SMLFile)


class TestSMLToDLMSBridge:
    def test_obis_bytes_to_str(self):
        assert SMLToDLMSBridge.obis_bytes_to_str(
            b"\x01\x00\x01\x08\x00\xff"
        ) == "1.0.1.8.0.255"

    def test_sml_entry_to_cosem(self):
        entry = SMLValueEntry(
            obis=b"\x01\x00\x01\x08\x00\xff",
            value=12345,
            scaler=-2,
            unit=27,
        )
        cosem = SMLToDLMSBridge.sml_entry_to_cosem(entry)
        assert cosem["obis"] == "1.0.1.8.0.255"
        assert cosem["value"] == 12345
        assert cosem["cosem_name"] == "Active Power +"

    def test_unknown_obis(self):
        entry = SMLValueEntry(obis=b"\x09\x09\x09\x09\x09\x09", value=0)
        cosem = SMLToDLMSBridge.sml_entry_to_cosem(entry)
        assert cosem["cosem_name"] == "Unknown"

    def test_parse_meter_data(self):
        # Minimal SML-like data
        data = b"\x1b\x1b\x1b\x1b"
        result = SMLToDLMSBridge.parse_meter_data(data)
        assert isinstance(result, list)


class TestSMLTags:
    def test_tag_values(self):
        assert SMLTag.END_OF_SML_FILE == 0x1b
        assert SMLTag.GET_OPEN_REQUEST == 0x01
        assert SMLTag.GET_CLOSE_RESPONSE == 0x04

    def test_signature_modes(self):
        assert SMLSignatureMode.NONE == 0
        assert SMLSignatureMode.AES_CMAC == 1
        assert SMLSignatureMode.RSA_SHA256 == 2


class TestSMLFile:
    def test_empty_file(self):
        f = SMLFile()
        assert len(f.messages) == 0
        assert f.get_value_entries() == []

    def test_add_message(self):
        f = SMLFile()
        msg = SMLMessage(tag=SMLTag.GET_OPEN_REQUEST, transaction_id=b"\x00\x00\x00\x01")
        f.messages.append(msg)
        assert len(f.messages) == 1
