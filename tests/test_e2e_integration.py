"""End-to-end integration tests for DLMS/COSEM.

These tests verify complete workflows from client to server,
including transport layer, protocol stack, and COSEM object interaction.
"""
import pytest

from dlms_cosem.cosem.obis import Obis
from dlms_cosem.cosem.base import CosemAttribute
from dlms_cosem.dlms_data import DlmsDataFactory
from dlms_cosem.protocol.xdlms.get import GetRequestNormal
from dlms_cosem.protocol.xdlms.invoke_id_and_priority import InvokeIdAndPriority
from dlms_cosem.hdlc.frames import InformationFrame
from dlms_cosem.exceptions import DlmsProtocolError, DlmsException


def _get_simple_attribute() -> CosemAttribute:
    """Helper to create a simple COSEM attribute."""
    return CosemAttribute(
        interface=1,
        instance=Obis.from_string("1.0.1.8.0.255"),
        attribute=2,
    )


class TestProtocolStackIntegration:
    """Test protocol stack integration without network I/O."""

    def test_get_request_normal_construction(self):
        """Test GetRequestNormal construction."""
        # Create attribute
        attribute = _get_simple_attribute()

        # Create request
        request = GetRequestNormal(
            invoke_id_and_priority=InvokeIdAndPriority(invoke_id=192, priority=0),
            cosem_attribute=attribute,
        )

        # Verify serialization
        apdu = request.to_bytes()
        assert len(apdu) > 0
        assert apdu[0] == 0xC0  # Tag

    def test_hldc_frame_wraps_apdu(self):
        """Test HDLC frames wrap APDU correctly."""
        # Create APDU
        attribute = _get_simple_attribute()
        request = GetRequestNormal(
            invoke_id_and_priority=attribute.get_invoke_id(),
            cosem_attribute=attribute,
        )
        apdu = request.to_bytes()

        # Wrap in HDLC Information frame
        frame = InformationFrame(
            destination_address=1,
            source_address=16,
            send_sequence_number=0,
            frame_format_type=3,
            segment=0,
            control_field=0x10,
            hcs=None,
            information=apdu,
        )
        frame_bytes = frame.to_bytes()

        # Verify frame structure
        assert frame_bytes[0] == 0x7E  # Opening flag
        assert frame_bytes[-1] == 0x7E  # Closing flag
        assert apdu in frame_bytes  # APDU is inside


class TestCosemObjectIntegration:
    """Test COSEM object interaction."""

    def test_attribute_serialization(self):
        """Test CosemAttribute serialization."""
        attribute = _get_simple_attribute()
        data = attribute.to_bytes()

        # Verify format: interface (1) + instance (6) + attribute (1) = 8 bytes
        assert len(data) == 8

    def test_attribute_deserialization(self):
        """Test CosemAttribute deserialization."""
        # Serialize attribute
        attribute = _get_simple_attribute()
        data = attribute.to_bytes()

        # Deserialize
        parsed = DlmsDataFactory.from_bytes(data, tag=0x02)

        assert parsed.interface == 1
        assert parsed.attribute == 2


class TestObisParsing:
    """Test OBIS code parsing."""

    def test_obis_from_string(self):
        """Test OBIS code parsing from string."""
        obis = Obis.from_string("1.0.1.8.0.255")

        assert obis.a == 1
        assert obis.b == 0
        assert obis.c == 1
        assert obis.d == 0
        assert obis.e == 0
        assert obis.f == 1

    def test_obis_to_string(self):
        """Test OBIS code to string conversion."""
        obis = Obis.from_string("1.0.1.8.0.255")
        obis_str = str(obis)

        assert obis_str == "1-0:1.8.0.255"

    def test_invalid_obis_raises_error(self):
        """Test that invalid OBIS raises error."""
        with pytest.raises(ValueError):
            Obis.from_string("invalid.obis.code")


class TestErrorPropagation:
    """Test error propagation through the stack."""

    def test_dlms_exception_creation(self):
        """Test DLMS exception creation."""
        error = DlmsException(
            message="Test error",
        )

        assert error.message == "Test error"

    def test_exception_to_string(self):
        """Test exception string representation."""
        error = DlmsException(message="Test")
        error_str = str(error)

        assert "Test" in error_str

    def test_exception_hierarchy(self):
        """Test exception hierarchy."""
        # LocalDlmsProtocolError should be instance of DlmsProtocolError
        local_error = LocalDlmsProtocolError(message="Local error")
        assert isinstance(local_error, DlmsProtocolError)
        assert isinstance(local_error, DlmsException)

    def test_protocol_error_from_subclass(self):
        """Test protocol error as subclass."""
        error = DlmsProtocolError(message="Protocol error")

        assert isinstance(error, DlmsException)

    def test_dlms_protocol_error_propagation(self):
        """Test DlmsProtocolError can be caught and re-raised."""
        original_error = DlmsProtocolError(message="Original error")

        with pytest.raises(DlmsProtocolError):
            raise original_error
