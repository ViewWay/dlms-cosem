from dateutil import parser

import pytest

from dlms_cosem import cosem, enumerations
from dlms_cosem.cosem import selective_access
from dlms_cosem.cosem.selective_access import EntryDescriptor, RangeDescriptor
from dlms_cosem.protocol.xdlms import GetRequestFactory


def test_capture_object_definition():
    x = selective_access.CaptureObject(
        cosem_attribute=cosem.CosemAttribute(
            interface=enumerations.CosemInterface.CLOCK,
            instance=cosem.Obis(0, 0, 1, 0, 0, 255),
            attribute=2,
        ),
        data_index=0,
    )

    assert x.to_bytes() == (
        b"\x02\x04"  # structure of 4 elements
        b"\x12\x00\x08"  # Clock interface class (unsigned long int)
        b"\t\x06\x00\x00\x01\x00\x00\xff"  # Clock instance octet string of 0.0.1.0.0.255
        b"\x0f\x02"  # attribute index  = 2 (integer)
        b"\x12\x00\x00"  # data index  = 0 (long unsigned)
    )


def test_range_descriptor1():
    data = (
        b"\xc0"  # Get request
        b"\x01"  # normal
        b"\xc1"  # invoke id and priority
        b"\x00\x07"  # Profile generic
        b"\x01\x00c\x01\x00\xff"  # 1.0.99.1.0.255
        b"\x02"  # Attribute 2 =  buffer
        b"\x01"  # non default value
        b"\x01"  # descriptor 1 (range-access)
        b"\x02\x04"  # strucutre of 4 elements
        b"\x02\x04"  # strucutre of 4 elements
        b"\x12\x00\x08"  # clock interface class
        b"\t\x06\x00\x00\x01\x00\x00\xff"  # clock instance name. 0.0.1.0.0.255
        b"\x0f\x02"  # attribute 2
        b"\x12\x00\x00"  # data index = 0
        b"\t\x0c\x07\xe2\x06\x01\xff\x00\x03\x00\xff\xff\x88\x80"  # from date
        b"\t\x0c\x07\xe5\x01\x06\xff\x00\x03\x00\xff\xff\xc4\x00"  # to date
        b"\x01\x00"  # all columns
    )
    assert data

    data2 = (
        b"\xc0\x01\xc1\x00\x07\x01\x00c\x01\x00\xff\x02\x01\x01"
        b"\x02\x04"
        b"\x02\x04"
        b"\x12\x00\x08"
        b"\t\x06\x00\x00\x01\x00\x00\xff"
        b"\x0f\x02"
        b"\x12\x00\x00"
        b"\t\x0c\x07\xe2\x02\x0c\xff\x00\x00\x00\x00\x80\x00\x00"
        b"\t\x0c\x07\xe3\x02\x0c\xff\x00\x00\x00\x00\x80\x00\x00"
        b"\x01\x00"
    )
    assert data2


def test_range_descriptor_to_bytes():
    rd = RangeDescriptor(
        restricting_object=selective_access.CaptureObject(
            cosem_attribute=cosem.CosemAttribute(
                interface=enumerations.CosemInterface.CLOCK,
                instance=cosem.Obis(0, 0, 1, 0, 0, 255),
                attribute=2,
            ),
            data_index=0,
        ),
        from_value=parser.parse("2020-01-01T00:03:00+02:00"),
        to_value=parser.parse("2020-01-06T00:03:00+01:00"),
    )
    data = b"\x01\x02\x04\x02\x04\x12\x00\x08\t\x06\x00\x00\x01\x00\x00\xff\x0f\x02\x12\x00\x00\t\x0c\x07\xe4\x01\x01\xff\x00\x03\x00\x00\xff\x88\x00\t\x0c\x07\xe4\x01\x06\xff\x00\x03\x00\x00\xff\xc4\x00\x01\x00"
    assert rd.to_bytes() == data


def test_parse_range_descriptor():
    """
    Profile: 1 (15 minutes profile)
    From: 01.10.2017 00:00
    To: 01.10.2017 01:00

    """

    data = b"\xc0\x01\xc1\x00\x07\x01\x00c\x01\x00\xff\x02\x01\x01\x02\x04\x02\x04\x12\x00\x08\t\x06\x00\x00\x01\x00\x00\xff\x0f\x02\x12\x00\x00\t\x0c\x07\xe1\n\x01\x07\x00\x00\x00\x00\xff\xc4\x80\t\x0c\x07\xe1\n\x01\x07\x01\x00\x00\x00\xff\xc4\x80\x01\x00"
    g = GetRequestFactory.from_bytes(data)

    access = (
        b"\x01"  # Optional value used
        b"\x01"  # Access selector
        b"\x02\x04"  # Structure of 4 elements
        b"\x02\x04"  # structure of 4 elements
        b"\x12\x00\x08"  # Clock interface class (unsigned long int)
        b"\t\x06\x00\x00\x01\x00\x00\xff"  # Clock instance octet string of 0.0.1.0.0.255
        b"\x0f\x02"  # attribute index  = 2 (integer)
        b"\x12\x00\x00"  # data index  = 0 (long unsigned)
        b"\t\x0c\x07\xe1\n\x01\x07\x00\x00\x00\x00\xff\xc4\x80"  # from date
        b"\t\x0c\x07\xe1\n\x01\x07\x01\x00\x00\x00\xff\xc4\x80"  # to date
        b"\x01\x00"  # selected_values empty array.
    )
    assert access

    access_selection = g.access_selection

    assert isinstance(access_selection, RangeDescriptor)
    assert access_selection.selected_values is None
    assert (
        access_selection.restricting_object.cosem_attribute.instance.to_string()
        == "0-0:1.0.0.255"
    )


class TestEntryDescriptor:
    """Tests for EntryDescriptor selective access."""

    def test_entry_descriptor_to_bytes(self):
        """Test encoding an EntryDescriptor."""
        ed = EntryDescriptor(
            from_entry=1,
            to_entry=10,
            from_selected_value=1,
            to_selected_value=5,
        )

        # Expected structure using DLMS data encoding:
        # 0x02 - access_descriptor (EntryDescriptor)
        # 0x04 - structure of 4 elements
        # 0x06 0x00 0x00 0x00 0x01 - from_entry (DoubleLongUnsignedData, no length byte)
        # 0x06 0x00 0x00 0x00 0x0A - to_entry (DoubleLongUnsignedData, no length byte)
        # 0x12 0x00 0x01 - from_selected_value (UnsignedLongData)
        # 0x12 0x00 0x05 - to_selected_value (UnsignedLongData)
        expected = (
            b"\x02\x04"
            b"\x06\x00\x00\x00\x01"
            b"\x06\x00\x00\x00\x0A"
            b"\x12\x00\x01"
            b"\x12\x00\x05"
        )
        assert ed.to_bytes() == expected

    def test_entry_descriptor_to_bytes_zero_means_highest(self):
        """Test that 0 for to_entry and to_selected_value means highest value."""
        ed = EntryDescriptor(
            from_entry=1,
            to_entry=0,  # 0 means highest possible
            from_selected_value=1,
            to_selected_value=0,  # 0 means highest possible
        )

        expected = (
            b"\x02\x04"
            b"\x06\x00\x00\x00\x01"
            b"\x06\x00\x00\x00\x00"
            b"\x12\x00\x01"
            b"\x12\x00\x00"
        )
        assert ed.to_bytes() == expected

    def test_entry_descriptor_from_bytes(self):
        """Test decoding an EntryDescriptor."""
        data = (
            b"\x02\x04"
            b"\x06\x00\x00\x00\x01"
            b"\x06\x00\x00\x00\x0A"
            b"\x12\x00\x01"
            b"\x12\x00\x05"
        )

        ed = EntryDescriptor.from_bytes(data)

        assert ed.from_entry == 1
        assert ed.to_entry == 10
        assert ed.from_selected_value == 1
        assert ed.to_selected_value == 5

    def test_entry_descriptor_encode_decode_roundtrip(self):
        """Test encoding and decoding an EntryDescriptor produces the same data."""
        original = EntryDescriptor(
            from_entry=5,
            to_entry=100,
            from_selected_value=2,
            to_selected_value=8,
        )

        encoded = original.to_bytes()
        decoded = EntryDescriptor.from_bytes(encoded)

        assert decoded.from_entry == original.from_entry
        assert decoded.to_entry == original.to_entry
        assert decoded.from_selected_value == original.from_selected_value
        assert decoded.to_selected_value == original.to_selected_value

    def test_entry_descriptor_invalid_access_descriptor(self):
        """Test that invalid access descriptor raises ValueError."""
        # Use access_descriptor = 1 (RangeDescriptor) instead of 2
        invalid_data = b"\x01\x04\x06\x00\x00\x00\x01\x06\x00\x00\x00\x0A\x12\x00\x01\x12\x00\x05"

        with pytest.raises(ValueError, match="is not valid for EntryDescriptor"):
            EntryDescriptor.from_bytes(invalid_data)

    def test_entry_descriptor_factory(self):
        """Test AccessDescriptorFactory with EntryDescriptor."""
        from dlms_cosem.cosem.selective_access import AccessDescriptorFactory

        data = (
            b"\x02\x04"
            b"\x06\x00\x00\x00\x01"
            b"\x06\x00\x00\x00\x0A"
            b"\x12\x00\x01"
            b"\x12\x00\x05"
        )

        descriptor = AccessDescriptorFactory.from_bytes(data)

        assert isinstance(descriptor, EntryDescriptor)
        assert descriptor.from_entry == 1
        assert descriptor.to_entry == 10
        assert descriptor.from_selected_value == 1
        assert descriptor.to_selected_value == 5
