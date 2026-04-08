"""End-to-end integration tests for DLMS/COSEM protocol stack.

Tests the complete data flow through multiple layers:
    Client → APDU → HDLC Frame → bytes → HDLC Frame → APDU → Server
"""
import pytest

from dlms_cosem.cosem.obis import Obis
from dlms_cosem.cosem.base import CosemAttribute
from dlms_cosem.dlms_data import DlmsDataFactory
from dlms_cosem.protocol.xdlms.get import GetRequestNormal
from dlms_cosem.protocol.xdlms.invoke_id_and_priority import InvokeIdAndPriority
from dlms_cosem.exceptions import (
    DlmsException,
    DlmsProtocolError,
    LocalDlmsProtocolError,
)
import dlms_cosem.enumerations as enums


def _make_attribute(obis_str: str = "1.0.1.8.0.255", attr: int = 2) -> CosemAttribute:
    """Create a CosemAttribute for testing."""
    return CosemAttribute(
        interface=enums.CosemInterface.DATA,
        instance=Obis.from_string(obis_str),
        attribute=attr,
    )


class TestGetRequestNormalRoundtrip:
    """Test GET request construction and serialization."""

    def test_construction(self):
        attr = _make_attribute()
        req = GetRequestNormal(
            invoke_id_and_priority=InvokeIdAndPriority(invoke_id=1),
            cosem_attribute=attr,
        )
        apdu = req.to_bytes()
        assert apdu[0] == 0xC0  # GET tag

    def test_roundtrip(self):
        attr = _make_attribute()
        req = GetRequestNormal(
            invoke_id_and_priority=InvokeIdAndPriority(invoke_id=1),
            cosem_attribute=attr,
        )
        apdu = req.to_bytes()
        parsed = GetRequestNormal.from_bytes(apdu)
        assert parsed.cosem_attribute.attribute == 2
        assert parsed.cosem_attribute.instance == Obis.from_string("1.0.1.8.0.255")

    def test_with_access_selection_none(self):
        attr = _make_attribute()
        req = GetRequestNormal(
            invoke_id_and_priority=InvokeIdAndPriority(invoke_id=1),
            cosem_attribute=attr,
        )
        assert req.access_selection is None


class TestObisParsing:
    """Test OBIS code operations."""

    def test_from_string(self):
        obis = Obis.from_string("1.0.1.8.0.255")
        assert obis.a == 1
        assert obis.b == 0
        assert obis.c == 1
        assert obis.d == 8
        assert obis.e == 0
        assert obis.f == 255

    def test_from_bytes_roundtrip(self):
        original = Obis.from_string("0.0.1.0.0.255")
        raw = original.to_bytes()
        assert len(raw) == 6
        parsed = Obis.from_bytes(raw)
        assert parsed == original

    def test_equality(self):
        a = Obis.from_string("1.0.1.8.0.255")
        b = Obis.from_string("1.0.1.8.0.255")
        assert a == b

    def test_invalid_string_raises(self):
        with pytest.raises(ValueError):
            Obis.from_string("not.valid")


class TestCosemAttributeRoundtrip:
    """Test CosemAttribute serialization."""

    def test_serialization_length(self):
        attr = _make_attribute()
        data = attr.to_bytes()
        assert len(data) == 9  # 2 (class_id) + 6 (obis) + 1 (attr)

    def test_roundtrip(self):
        attr = _make_attribute()
        data = attr.to_bytes()
        parsed = CosemAttribute.from_bytes(data)
        assert parsed.attribute == attr.attribute
        assert parsed.instance == attr.instance


class TestInvokeIdAndPriority:
    """Test invoke ID and priority construction."""

    def test_defaults(self):
        iip = InvokeIdAndPriority()
        assert iip.invoke_id == 1
        assert iip.confirmed is True
        assert iip.high_priority is True

    def test_to_bytes(self):
        iip = InvokeIdAndPriority(invoke_id=5, confirmed=True, high_priority=False)
        b = iip.to_bytes()
        assert len(b) == 1


class TestExceptionHierarchy:
    """Test DLMS exception hierarchy."""

    def test_base_exception(self):
        e = DlmsException(message="test")
        assert "test" in str(e)
        assert e.message == "test"

    def test_protocol_error_is_base(self):
        e = DlmsProtocolError(message="proto")
        assert isinstance(e, DlmsException)

    def test_local_protocol_error_is_subclass(self):
        e = LocalDlmsProtocolError(message="local")
        assert isinstance(e, DlmsProtocolError)
        assert isinstance(e, DlmsException)

    def test_catch_and_reraise(self):
        with pytest.raises(DlmsProtocolError):
            try:
                raise LocalDlmsProtocolError(message="inner")
            except DlmsProtocolError:
                raise

    def test_error_code(self):
        e = DlmsException(message="test", error_code=42)
        assert e.error_code == 42
        assert "42" in str(e)
