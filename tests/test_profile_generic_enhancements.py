"""
Tests for Profile Generic enhancements.

Tests for ReadByRange, ReadByEntry, and buffer parser enhancements.
"""
from datetime import datetime

import pytest

from dlms_cosem import cosem, enumerations
from dlms_cosem.cosem.capture_object import CaptureObject
from dlms_cosem.cosem.selective_access import EntryDescriptor, RangeDescriptor
from dlms_cosem.parsers import ColumnValue, ProfileGenericBufferParser


class TestRangeDescriptor:
    """Tests for RangeDescriptor functionality."""

    def test_create_range_descriptor(self):
        """Test creating a RangeDescriptor."""
        restricting_object = CaptureObject(
            cosem_attribute=cosem.CosemAttribute(
                interface=enumerations.CosemInterface.PROFILE_GENERIC,
                instance=cosem.Obis.from_string("1.0.99.1.0.255"),
                attribute=3,
            ),
            data_index=0,
        )
        from_value = datetime(2024, 1, 1, 0, 0, 0)
        to_value = datetime(2024, 1, 31, 23, 59, 59)

        descriptor = RangeDescriptor(
            restricting_object=restricting_object,
            from_value=from_value,
            to_value=to_value,
        )

        assert descriptor.restricting_object == restricting_object
        assert descriptor.from_value == from_value
        assert descriptor.to_value == to_value
        assert descriptor.selected_values is None

    def test_encode_range_descriptor(self):
        """Test encoding a RangeDescriptor to bytes."""
        restricting_object = CaptureObject(
            cosem_attribute=cosem.CosemAttribute(
                interface=enumerations.CosemInterface.PROFILE_GENERIC,
                instance=cosem.Obis.from_string("1.0.99.1.0.255"),
                attribute=3,
            ),
            data_index=0,
        )
        from_value = datetime(2024, 1, 1, 0, 0, 0)
        to_value = datetime(2024, 1, 31, 23, 59, 59)

        descriptor = RangeDescriptor(
            restricting_object=restricting_object,
            from_value=from_value,
            to_value=to_value,
        )

        encoded = descriptor.to_bytes()
        assert encoded[0] == descriptor.ACCESS_DESCRIPTOR
        assert len(encoded) > 10

    def test_decode_range_descriptor(self):
        """Test decoding a RangeDescriptor from bytes."""
        restricting_object = CaptureObject(
            cosem_attribute=cosem.CosemAttribute(
                interface=enumerations.CosemInterface.PROFILE_GENERIC,
                instance=cosem.Obis.from_string("1.0.99.1.0.255"),
                attribute=3,
            ),
            data_index=0,
        )
        from_value = datetime(2024, 1, 1, 0, 0, 0)
        to_value = datetime(2024, 1, 31, 23, 59, 59)

        original = RangeDescriptor(
            restricting_object=restricting_object,
            from_value=from_value,
            to_value=to_value,
        )

        encoded = original.to_bytes()
        decoded = RangeDescriptor.from_bytes(encoded)

        assert decoded.from_value.year == 2024
        assert decoded.from_value.month == 1
        assert decoded.from_value.day == 1


class TestEntryDescriptor:
    """Tests for EntryDescriptor functionality."""

    def test_create_entry_descriptor_defaults(self):
        """Test creating an EntryDescriptor with default values."""
        descriptor = EntryDescriptor(from_entry=1)

        assert descriptor.from_entry == 1
        assert descriptor.to_entry == 0  # 0 means to the end
        assert descriptor.from_selected_value == 1
        assert descriptor.to_selected_value == 0  # 0 means to the end

    def test_create_entry_descriptor_all_columns(self):
        """Test creating an EntryDescriptor that gets all columns."""
        descriptor = EntryDescriptor(
            from_entry=1,
            to_entry=100,
            from_selected_value=1,
            to_selected_value=0,
        )

        assert descriptor.from_entry == 1
        assert descriptor.to_entry == 100
        assert descriptor.from_selected_value == 1
        assert descriptor.to_selected_value == 0

    def test_create_entry_descriptor_column_filter(self):
        """Test creating an EntryDescriptor with column filtering."""
        descriptor = EntryDescriptor(
            from_entry=1,
            to_entry=100,
            from_selected_value=1,
            to_selected_value=5,
        )

        assert descriptor.from_selected_value == 1
        assert descriptor.to_selected_value == 5

    def test_encode_entry_descriptor(self):
        """Test encoding an EntryDescriptor to bytes."""
        descriptor = EntryDescriptor(
            from_entry=1,
            to_entry=100,
            from_selected_value=1,
            to_selected_value=5,
        )

        encoded = descriptor.to_bytes()
        assert encoded[0] == descriptor.ACCESS_DESCRIPTOR
        assert encoded[1] == 0x04  # 4 elements

    def test_decode_entry_descriptor(self):
        """Test decoding an EntryDescriptor from bytes."""
        original = EntryDescriptor(
            from_entry=1,
            to_entry=100,
            from_selected_value=1,
            to_selected_value=5,
        )

        encoded = original.to_bytes()
        decoded = EntryDescriptor.from_bytes(encoded)

        assert decoded.from_entry == 1
        assert decoded.to_entry == 100
        assert decoded.from_selected_value == 1
        assert decoded.to_selected_value == 5

    def test_encode_decode_roundtrip(self):
        """Test round-trip encoding/decoding of EntryDescriptor."""
        original = EntryDescriptor(
            from_entry=10,
            to_entry=50,
            from_selected_value=2,
            to_selected_value=8,
        )

        encoded = original.to_bytes()
        decoded = EntryDescriptor.from_bytes(encoded)

        assert decoded.from_entry == original.from_entry
        assert decoded.to_entry == original.to_entry
        assert decoded.from_selected_value == original.from_selected_value
        assert decoded.to_selected_value == original.to_selected_value


class TestProfileGenericBufferParser:
    """Tests for ProfileGenericBufferParser enhancements."""

    @pytest.fixture
    def sample_capture_objects(self):
        """Create sample capture objects for testing."""
        return [
            cosem.CosemAttribute(
                interface=enumerations.CosemInterface.CLOCK,
                instance=cosem.Obis.from_string("1.0.99.1.0.255"),
                attribute=2,
            ),
            cosem.CosemAttribute(
                interface=enumerations.CosemInterface.REGISTER,
                instance=cosem.Obis.from_string("1.0.1.1.0.255"),
                attribute=2,
            ),
            cosem.CosemAttribute(
                interface=enumerations.CosemInterface.REGISTER,
                instance=cosem.Obis.from_string("1.0.1.2.0.255"),
                attribute=2,
            ),
        ]

    def test_parser_with_column_filter(self, sample_capture_objects):
        """Test creating a parser with column filtering."""
        parser = ProfileGenericBufferParser.with_column_filter(
            capture_objects=sample_capture_objects,
            capture_period=15,
            from_column=1,
            to_column=2,  # Only first 2 columns
        )

        assert parser.from_column == 1
        assert parser.to_column == 2

        filtered = parser._get_filtered_columns()
        assert len(filtered) == 2
        assert filtered[0].interface == enumerations.CosemInterface.CLOCK
        assert filtered[1].interface == enumerations.CosemInterface.REGISTER

    def test_parser_with_column_filter_to_end(self, sample_capture_objects):
        """Test creating a parser with column filter to the end."""
        parser = ProfileGenericBufferParser.with_column_filter(
            capture_objects=sample_capture_objects,
            capture_period=15,
            from_column=2,
            to_column=0,  # From column 2 to the end
        )

        assert parser.from_column == 2
        assert parser.to_column is None

        filtered = parser._get_filtered_columns()
        assert len(filtered) == 2  # Columns 2 and 3
        assert filtered[0].interface == enumerations.CosemInterface.REGISTER

    def test_parser_without_column_filter(self, sample_capture_objects):
        """Test creating a parser without column filtering."""
        parser = ProfileGenericBufferParser(
            capture_objects=sample_capture_objects,
            capture_period=15,
        )

        assert parser.from_column is None
        assert parser.to_column is None

        filtered = parser._get_filtered_columns()
        assert len(filtered) == 3

    def test_filter_entry_columns(self, sample_capture_objects):
        """Test filtering entry columns."""
        parser = ProfileGenericBufferParser(
            capture_objects=sample_capture_objects,
            capture_period=15,
            from_column=1,
            to_column=2,
        )

        entry = [b"data1", b"data2", b"data3"]
        filtered = parser._filter_entry_columns(entry)

        assert len(filtered) == 2
        assert filtered == [b"data1", b"data2"]

    def test_filter_entry_columns_to_end(self, sample_capture_objects):
        """Test filtering entry columns from index to end."""
        parser = ProfileGenericBufferParser(
            capture_objects=sample_capture_objects,
            capture_period=15,
            from_column=2,
            to_column=0,
        )

        entry = [b"data1", b"data2", b"data3"]
        filtered = parser._filter_entry_columns(entry)

        assert len(filtered) == 2
        assert filtered == [b"data2", b"data3"]


class TestProfileGenericIntegration:
    """Integration tests for Profile Generic enhancements."""

    def test_range_descriptor_integration(self):
        """Test RangeDescriptor can be used with GetRequest."""
        from dlms_cosem.protocol.xdlms.get import GetRequestNormal
        from dlms_cosem.protocol.xdlms.invoke_id_and_priority import (
            InvokeIdAndPriority,
        )

        restricting_object = CaptureObject(
            cosem_attribute=cosem.CosemAttribute(
                interface=enumerations.CosemInterface.PROFILE_GENERIC,
                instance=cosem.Obis.from_string("1.0.99.1.0.255"),
                attribute=3,
            ),
            data_index=0,
        )
        range_descriptor = RangeDescriptor(
            restricting_object=restricting_object,
            from_value=datetime(2024, 1, 1),
            to_value=datetime(2024, 1, 31),
        )

        request = GetRequestNormal(
            cosem_attribute=cosem.CosemAttribute(
                interface=enumerations.CosemInterface.PROFILE_GENERIC,
                instance=cosem.Obis.from_string("1.0.99.1.0.255"),
                attribute=2,
            ),
            access_selection=range_descriptor,
            invoke_id_and_priority=InvokeIdAndPriority(),
        )

        assert request.access_selection == range_descriptor
        encoded = request.to_bytes()
        assert len(encoded) > 0

    def test_entry_descriptor_integration(self):
        """Test EntryDescriptor can be used with GetRequest."""
        from dlms_cosem.protocol.xdlms.get import GetRequestNormal
        from dlms_cosem.protocol.xdlms.invoke_id_and_priority import (
            InvokeIdAndPriority,
        )

        entry_descriptor = EntryDescriptor(
            from_entry=1,
            to_entry=100,
            from_selected_value=1,
            to_selected_value=5,
        )

        request = GetRequestNormal(
            cosem_attribute=cosem.CosemAttribute(
                interface=enumerations.CosemInterface.PROFILE_GENERIC,
                instance=cosem.Obis.from_string("1.0.99.1.0.255"),
                attribute=2,
            ),
            access_selection=entry_descriptor,
            invoke_id_and_priority=InvokeIdAndPriority(),
        )

        assert request.access_selection == entry_descriptor
        encoded = request.to_bytes()
        assert len(encoded) > 0
