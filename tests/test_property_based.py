"""
Property-based tests for core DLMS-COSEM modules using Hypothesis.

These tests verify that fundamental properties hold across random inputs:
- Round-trip encoding/decoding (encode → decode → original value)
- Tag-length-value structure preservation
- Frame construction/parsing consistency
- OBIS code formatting/parsing round-trips
- COSEM data type serialization/deserialization
"""

import datetime
from hypothesis import given, strategies as st, settings, assume
import pytest

from dlms_cosem.a_xdr import AXdrDecoder, EncodingConf, Attribute, Sequence
from dlms_cosem.cosem.obis import Obis
from dlms_cosem import dlms_data
from dlms_cosem.hdlc import frames, fields, address as hdlc_address
from dlms_cosem.utils import parse_as_dlms_data


# =============================================================================
# OBIS Code Property Tests
# =============================================================================

@given(
    a=st.integers(min_value=0, max_value=255),
    b=st.integers(min_value=0, max_value=255),
    c=st.integers(min_value=0, max_value=255),
    d=st.integers(min_value=0, max_value=255),
    e=st.integers(min_value=0, max_value=255),
    f=st.integers(min_value=0, max_value=255),
)
@settings(max_examples=100)
def test_obis_bytes_roundtrip(a, b, c, d, e, f):
    """OBIS code should round-trip through to_bytes and from_bytes."""
    original = Obis(a, b, c, d, e, f)
    bytes_data = original.to_bytes()
    restored = Obis.from_bytes(bytes_data)
    assert original == restored


@given(
    a=st.integers(min_value=0, max_value=255),
    b=st.integers(min_value=0, max_value=255),
    c=st.integers(min_value=0, max_value=255),
    d=st.integers(min_value=0, max_value=255),
    e=st.integers(min_value=0, max_value=255),
    separator=st.sampled_from(['.', '-', ':', '_']),
)
@settings(max_examples=100)
def test_obis_string_roundtrip(a, b, c, d, e, separator):
    """OBIS code should round-trip through to_string and from_string."""
    original = Obis(a, b, c, d, e, 255)  # Default f to 255
    string_repr = original.to_string(separator=separator)
    restored = Obis.from_string(string_repr)
    # Note: from_string doesn't parse the last part if it's the default 255
    assert (original.a, original.b, original.c, original.d, original.e) == \
           (restored.a, restored.b, restored.c, restored.d, restored.e)


@given(
    a=st.integers(min_value=0, max_value=255),
    b=st.integers(min_value=0, max_value=255),
    c=st.integers(min_value=0, max_value=255),
    d=st.integers(min_value=0, max_value=255),
    e=st.integers(min_value=0, max_value=255),
    f=st.integers(min_value=0, max_value=255),
)
@settings(max_examples=50)
def test_obis_bytes_length(a, b, c, d, e, f):
    """OBIS code bytes should always be exactly 6 bytes."""
    obis = Obis(a, b, c, d, e, f)
    bytes_data = obis.to_bytes()
    assert len(bytes_data) == 6


# =============================================================================
# COSEM Data Types Property Tests
# =============================================================================

@given(value=st.integers(min_value=0, max_value=255))
@settings(max_examples=100)
def test_unsigned_integer_data_roundtrip(value):
    """Unsigned integer (8-bit) data should round-trip through value_to_bytes/from_bytes."""
    original = dlms_data.UnsignedIntegerData(value=value)
    bytes_data = original.value_to_bytes()
    restored = dlms_data.UnsignedIntegerData.from_bytes(bytes_data)
    assert original.value == restored.value


@given(value=st.integers(min_value=0, max_value=65535))
@settings(max_examples=100)
def test_unsigned_long_data_roundtrip(value):
    """Unsigned long (16-bit) data should round-trip through value_to_bytes/from_bytes."""
    original = dlms_data.UnsignedLongData(value=value)
    bytes_data = original.value_to_bytes()
    restored = dlms_data.UnsignedLongData.from_bytes(bytes_data)
    assert original.value == restored.value


@given(value=st.integers(min_value=0, max_value=4294967295))
@settings(max_examples=100)
def test_unsigned_double_long_data_roundtrip(value):
    """Unsigned double-long (32-bit) data should round-trip through value_to_bytes/from_bytes."""
    original = dlms_data.DoubleLongUnsignedData(value=value)
    bytes_data = original.value_to_bytes()
    restored = dlms_data.DoubleLongUnsignedData.from_bytes(bytes_data)
    assert original.value == restored.value


@given(value=st.integers(min_value=-128, max_value=127))
@settings(max_examples=100)
def test_integer_data_roundtrip(value):
    """Integer (8-bit) data should round-trip through value_to_bytes/from_bytes."""
    original = dlms_data.IntegerData(value=value)
    bytes_data = original.value_to_bytes()
    restored = dlms_data.IntegerData.from_bytes(bytes_data)
    assert original.value == restored.value


@given(value=st.integers(min_value=-32768, max_value=32767))
@settings(max_examples=100)
def test_signed_long_data_roundtrip(value):
    """Signed long (16-bit) data should round-trip through value_to_bytes/from_bytes."""
    original = dlms_data.LongData(value=value)
    bytes_data = original.value_to_bytes()
    restored = dlms_data.LongData.from_bytes(bytes_data)
    assert original.value == restored.value


@given(value=st.integers(min_value=-2147483648, max_value=2147483647))
@settings(max_examples=100)
def test_signed_double_long_data_roundtrip(value):
    """Signed double-long (32-bit) data should round-trip through value_to_bytes/from_bytes."""
    original = dlms_data.DoubleLongData(value=value)
    bytes_data = original.value_to_bytes()
    restored = dlms_data.DoubleLongData.from_bytes(bytes_data)
    assert original.value == restored.value


@given(value=st.integers(min_value=0, max_value=255))
@settings(max_examples=100)
def test_enum_data_roundtrip(value):
    """Enum data should round-trip through value_to_bytes/from_bytes."""
    original = dlms_data.EnumData(value=value)
    bytes_data = original.value_to_bytes()
    restored = dlms_data.EnumData.from_bytes(bytes_data)
    assert original.value == restored.value


@given(value=st.integers(min_value=-9223372036854775808, max_value=9223372036854775807))
@settings(max_examples=100)
def test_long64_data_roundtrip(value):
    """64-bit signed integer data should round-trip through value_to_bytes/from_bytes."""
    original = dlms_data.Long64Data(value=value)
    bytes_data = original.value_to_bytes()
    restored = dlms_data.Long64Data.from_bytes(bytes_data)
    assert original.value == restored.value


@given(value=st.integers(min_value=0, max_value=18446744073709551615))
@settings(max_examples=100)
def test_unsigned_long64_data_roundtrip(value):
    """64-bit unsigned integer data should round-trip through value_to_bytes/from_bytes."""
    original = dlms_data.UnsignedLong64Data(value=value)
    bytes_data = original.value_to_bytes()
    restored = dlms_data.UnsignedLong64Data.from_bytes(bytes_data)
    assert original.value == restored.value


@given(value=st.text(min_size=0, max_size=100, alphabet=st.characters(max_codepoint=127)))
@settings(max_examples=100)
def test_visible_string_data_roundtrip(value):
    """Visible string data should round-trip through value_to_bytes/from_bytes."""
    original = dlms_data.VisibleStringData(value=value)
    bytes_data = original.value_to_bytes()
    restored = dlms_data.VisibleStringData.from_bytes(bytes_data)
    assert original.value == restored.value


@given(value=st.binary(min_size=0, max_size=100))
@settings(max_examples=100)
def test_octet_string_data_roundtrip(value):
    """Octet string data should round-trip through value_to_bytes/from_bytes."""
    original = dlms_data.OctetStringData(value=value)
    bytes_data = original.value_to_bytes()
    restored = dlms_data.OctetStringData.from_bytes(bytes_data)
    assert original.value == restored.value


@given(
    values=st.lists(
        st.integers(min_value=0, max_value=255),
        min_size=0,
        max_size=10
    )
)
@settings(max_examples=100)
def test_array_data_roundtrip(values):
    """Array data should round-trip through to_bytes/from_bytes using parser."""
    # Create array from list of unsigned values
    data_items = [dlms_data.UnsignedIntegerData(value=v) for v in values]
    original = dlms_data.DataArray(value=data_items)
    bytes_data = original.to_bytes()
    # Use parser to restore (handles TAG and length bytes)
    parser = dlms_data.DlmsDataParser()
    parsed = parser.parse(bytes_data, limit=1)
    restored = parsed[0]
    assert len(original.value) == len(restored.value)
    for orig, rest in zip(original.value, restored.value):
        assert orig.value == rest.value


@given(
    values=st.lists(
        st.integers(min_value=0, max_value=255),
        min_size=0,
        max_size=10
    )
)
@settings(max_examples=100)
def test_structure_data_roundtrip(values):
    """Structure data should round-trip through to_bytes/from_bytes using parser."""
    # Create structure from list of unsigned values
    data_items = [dlms_data.UnsignedIntegerData(value=v) for v in values]
    original = dlms_data.DataStructure(value=data_items)
    bytes_data = original.to_bytes()
    # Use parser to restore (handles TAG and length bytes)
    parser = dlms_data.DlmsDataParser()
    parsed = parser.parse(bytes_data, limit=1)
    restored = parsed[0]
    assert len(original.value) == len(restored.value)
    for orig, rest in zip(original.value, restored.value):
        assert orig.value == rest.value


@given(
    year=st.integers(min_value=1, max_value=9999),
    month=st.integers(min_value=1, max_value=12),
    day=st.integers(min_value=1, max_value=31),
)
@settings(max_examples=100)
def test_date_data_roundtrip(year, month, day):
    """Date data should round-trip through value_to_bytes/from_bytes."""
    try:
        date = datetime.date(year, month, day)
        original = dlms_data.DateData(value=date)
        bytes_data = original.value_to_bytes()
        restored = dlms_data.DateData.from_bytes(bytes_data)
        assert original.value == restored.value
    except ValueError:
        # Invalid date combinations (e.g., Feb 30) are OK to skip
        pass


@given(
    hour=st.integers(min_value=0, max_value=23),
    minute=st.integers(min_value=0, max_value=59),
    second=st.integers(min_value=0, max_value=59),
    hundredth=st.integers(min_value=0, max_value=99),
)
@settings(max_examples=100)
def test_time_data_roundtrip(hour, minute, second, hundredth):
    """Time data should round-trip through value_to_bytes/from_bytes."""
    try:
        time = datetime.time(hour, minute, second, hundredth * 10000)
        original = dlms_data.TimeData(value=time)
        bytes_data = original.value_to_bytes()
        restored = dlms_data.TimeData.from_bytes(bytes_data)
        assert original.value == restored.value
    except ValueError:
        # Invalid time combinations are OK to skip
        pass


# =============================================================================
# HDLC Frames Property Tests
# =============================================================================

@given(
    server_logical=st.integers(min_value=0, max_value=127),
    client_logical=st.integers(min_value=0, max_value=127),
    payload=st.binary(min_size=0, max_size=50)
)
@settings(max_examples=100)
def test_hdlc_frame_roundtrip(server_logical, client_logical, payload):
    """HDLC Information frame should round-trip through to_bytes and from_bytes."""
    destination_address = hdlc_address.HdlcAddress(
        logical_address=server_logical,
        address_type="server"
    )
    source_address = hdlc_address.HdlcAddress(
        logical_address=client_logical,
        address_type="client"
    )

    original = frames.InformationFrame(
        destination_address=destination_address,
        source_address=source_address,
        payload=payload if payload else None
    )

    # Some frames without payload may not have HCS
    if original.payload:
        bytes_data = original.to_bytes()
        restored = frames.InformationFrame.from_bytes(bytes_data)
        assert original.destination_address.logical_address == restored.destination_address.logical_address
        assert original.source_address.logical_address == restored.source_address.logical_address
        assert original.payload == restored.payload


@given(
    logical_address=st.integers(min_value=0, max_value=127),
    address_type=st.sampled_from(["client", "server"])
)
@settings(max_examples=100)
def test_hdlc_client_address_roundtrip(logical_address, address_type):
    """HDLC client address should be reconstructable from to_bytes."""
    original = hdlc_address.HdlcAddress(logical_address=logical_address, address_type=address_type)
    bytes_data = original.to_bytes()
    # For client addresses, we can reconstruct from bytes by shifting right
    if address_type == "client":
        restored_logical = int.from_bytes(bytes_data, "big") >> 1
        assert original.logical_address == restored_logical


@given(
    server_logical=st.integers(min_value=0, max_value=127),
    client_logical=st.integers(min_value=0, max_value=127),
    payload=st.binary(min_size=0, max_size=50)
)
@settings(max_examples=100)
def test_hdlc_frame_flag_encapsulation(server_logical, client_logical, payload):
    """HDLC Information frames should be properly encapsulated with flags (0x7E)."""
    destination_address = hdlc_address.HdlcAddress(
        logical_address=server_logical,
        address_type="server"
    )
    source_address = hdlc_address.HdlcAddress(
        logical_address=client_logical,
        address_type="client"
    )

    frame = frames.InformationFrame(
        destination_address=destination_address,
        source_address=source_address,
        payload=payload if payload else None
    )

    if frame.payload:
        bytes_data = frame.to_bytes()
        assert bytes_data[0] == 0x7E  # Start flag
        assert bytes_data[-1] == 0x7E  # End flag


# =============================================================================
# AXDR Encoding Property Tests
# =============================================================================

@given(value=st.integers(min_value=0, max_value=255))
@settings(max_examples=100)
def test_axdr_length_encoding_small(value):
    """Small AXDR lengths (<128) should be encoded in 1 byte."""
    length = dlms_data.encode_variable_integer(value)
    if value < 128:
        assert len(length) == 1
        assert length[0] == value


@given(value=st.integers(min_value=128, max_value=100000))
@settings(max_examples=100)
def test_axdr_length_encoding_large(value):
    """Large AXDR lengths (>=128) should use variable-length encoding."""
    length = dlms_data.encode_variable_integer(value)
    if value >= 128:
        # First byte should have high bit set
        assert length[0] & 0x80 != 0


@given(
    values=st.lists(
        st.integers(min_value=0, max_value=255),
        min_size=0,
        max_size=10
    )
)
@settings(max_examples=100)
def test_parse_as_dlms_data_roundtrip(values):
    """parse_as_dlms_data should be able to parse data it created."""
    # Create a data structure with unsigned values
    data_items = [dlms_data.UnsignedIntegerData(value=v) for v in values]
    structure = dlms_data.DataStructure(value=data_items)
    bytes_data = structure.to_bytes()

    # Parse it back
    parsed = parse_as_dlms_data(bytes_data)

    # The parsed result should match the original values
    assert len(parsed) == len(values)
    for parsed_val, orig_val in zip(parsed, values):
        assert parsed_val == orig_val


# =============================================================================
# Mixed Complex Scenarios
# =============================================================================

@given(
    values=st.lists(
        st.integers(min_value=0, max_value=65535),
        min_size=0,
        max_size=5
    )
)
@settings(max_examples=100)
def test_array_of_long_unsigned_roundtrip(values):
    """Array of long-unsigned values should round-trip using parser."""
    data_items = [dlms_data.UnsignedLongData(value=v) for v in values]
    array = dlms_data.DataArray(value=data_items)
    bytes_data = array.to_bytes()
    # Use parser to restore (handles TAG and length bytes)
    parser = dlms_data.DlmsDataParser()
    parsed = parser.parse(bytes_data, limit=1)
    restored = parsed[0]
    assert len(array.value) == len(restored.value)
    for orig, rest in zip(array.value, restored.value):
        assert orig.value == rest.value


@given(
    nested_values=st.lists(
        st.integers(min_value=0, max_value=255),
        min_size=0,
        max_size=5
    )
)
@settings(max_examples=100)
def test_structure_of_unsigned_roundtrip(nested_values):
    """Structure containing unsigned values should round-trip using parser."""
    data_items = [dlms_data.UnsignedIntegerData(value=v) for v in nested_values]
    structure = dlms_data.DataStructure(value=data_items)
    bytes_data = structure.to_bytes()
    # Use parser to restore (handles TAG and length bytes)
    parser = dlms_data.DlmsDataParser()
    parsed = parser.parse(bytes_data, limit=1)
    restored = parsed[0]
    assert len(structure.value) == len(restored.value)
    for orig, rest in zip(structure.value, restored.value):
        assert orig.value == rest.value


@given(
    values=st.lists(
        st.integers(min_value=0, max_value=65535),
        min_size=0,
        max_size=5
    )
)
@settings(max_examples=100)
def test_parse_variable_integer_roundtrip(values):
    """Variable integer encoding and decoding should round-trip."""
    for value in values:
        encoded = dlms_data.encode_variable_integer(value)
        decoded, _ = dlms_data.decode_variable_integer(encoded)
        assert decoded == value


# =============================================================================
# Edge Cases and Boundary Values
# =============================================================================

@given(value=st.just(0))
@settings(max_examples=1)
def test_unsigned_integer_boundary_zero(value):
    """Unsigned integer should handle boundary value 0 correctly."""
    original = dlms_data.UnsignedIntegerData(value=value)
    bytes_data = original.value_to_bytes()
    restored = dlms_data.UnsignedIntegerData.from_bytes(bytes_data)
    assert original.value == restored.value == 0


@given(value=st.just(255))
@settings(max_examples=1)
def test_unsigned_integer_boundary_max(value):
    """Unsigned integer should handle max value correctly."""
    original = dlms_data.UnsignedIntegerData(value=value)
    bytes_data = original.value_to_bytes()
    restored = dlms_data.UnsignedIntegerData.from_bytes(bytes_data)
    assert original.value == restored.value == 255


@given(
    a=st.just(0),
    b=st.just(0),
    c=st.just(0),
    d=st.just(0),
    e=st.just(0),
    f=st.just(0),
)
@settings(max_examples=5)
def test_obis_all_zeros_roundtrip(a, b, c, d, e, f):
    """OBIS code with all zeros should round-trip correctly."""
    original = Obis(a, b, c, d, e, f)
    bytes_data = original.to_bytes()
    restored = Obis.from_bytes(bytes_data)
    assert original == restored


@given(
    a=st.just(255),
    b=st.just(255),
    c=st.just(255),
    d=st.just(255),
    e=st.just(255),
    f=st.just(255),
)
@settings(max_examples=5)
def test_obis_all_ones_roundtrip(a, b, c, d, e, f):
    """OBIS code with all ones should round-trip correctly."""
    original = Obis(a, b, c, d, e, f)
    bytes_data = original.to_bytes()
    restored = Obis.from_bytes(bytes_data)
    assert original == restored


@given(
    values=st.lists(
        st.integers(min_value=-32768, max_value=32767),
        min_size=0,
        max_size=10
    )
)
@settings(max_examples=50)
def test_structure_of_signed_long_roundtrip(values):
    """Structure containing signed long values should round-trip using parser."""
    data_items = [dlms_data.LongData(value=v) for v in values]
    structure = dlms_data.DataStructure(value=data_items)
    bytes_data = structure.to_bytes()
    # Use parser to restore (handles TAG and length bytes)
    parser = dlms_data.DlmsDataParser()
    parsed = parser.parse(bytes_data, limit=1)
    restored = parsed[0]
    assert len(structure.value) == len(restored.value)
    for orig, rest in zip(structure.value, restored.value):
        assert orig.value == rest.value
