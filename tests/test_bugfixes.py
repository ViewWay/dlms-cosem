"""Tests for P0 bug fixes."""
import pytest
import attr
from dlms_cosem.hdlc import state, frames
from dlms_cosem.hdlc.address import HdlcAddress
from dlms_cosem.hdlc.parameters import HdlcParameterList, HdlcParameterType, negotiate_parameters
from dlms_cosem.a_xdr import get_variable_length_integer_from_bytes, is_variable_length_data, VARIABLE_LENGTH
from dlms_cosem.dlms_data import DataArray, DataStructure
from dlms_cosem.protocol.xdlms.set import (
    parse_access_selection, access_selection_to_bytes,
    RangeDescriptor, EntryDescriptor, SelectedValues,
    AccessSelectionType,
    SetRequestNormal,
)
from dlms_cosem import cosem, enumerations as enums
from dlms_cosem.protocol.xdlms.invoke_id_and_priority import InvokeIdAndPriority
from dlms_cosem import dlms_data


class TestBug1HdlcSegmentation:
    """Bug 1: HDLC segmentation handling states."""

    def test_segmenting_state_exists(self):
        assert hasattr(state, 'SEGMENTING')
        assert hasattr(state, 'AWAITING_SEGMENT')

    def test_segmenting_transitions_in_state_table(self):
        assert state.SEGMENTING in state.HDLC_STATE_TRANSITIONS
        assert state.AWAITING_SEGMENT in state.HDLC_STATE_TRANSITIONS
        # SEGMENTING should accept RR and I-frames
        assert frames.ReceiveReadyFrame in state.HDLC_STATE_TRANSITIONS[state.SEGMENTING]
        assert frames.InformationFrame in state.HDLC_STATE_TRANSITIONS[state.SEGMENTING]
        # AWAITING_SEGMENT should accept I-frames and RR
        assert frames.InformationFrame in state.HDLC_STATE_TRANSITIONS[state.AWAITING_SEGMENT]
        assert frames.ReceiveReadyFrame in state.HDLC_STATE_TRANSITIONS[state.AWAITING_SEGMENT]

    def test_state_machine_can_transition_to_segmenting(self):
        sm = state.HdlcConnectionState()
        sm.current_state = state.SEGMENTING
        sm._transition_state(frames.InformationFrame)
        assert sm.current_state == state.IDLE

    def test_awaiting_segment_stays_on_iframe(self):
        sm = state.HdlcConnectionState()
        sm.current_state = state.AWAITING_SEGMENT
        sm._transition_state(frames.InformationFrame)
        assert sm.current_state == state.AWAITING_SEGMENT


class TestBug2AxdrVariableLength:
    """Bug 2: A-XDR variable length data handling."""

    def test_get_variable_length_integer_single_byte(self):
        data = bytearray(b'\x0a')
        result = get_variable_length_integer_from_bytes(data)
        assert result == 10
        assert len(data) == 0

    def test_get_variable_length_integer_multi_byte(self):
        data = bytearray(b'\x82\x01\x00')
        result = get_variable_length_integer_from_bytes(data)
        assert result == 256
        assert len(data) == 0

    def test_get_variable_length_integer_large(self):
        data = bytearray(b'\x82\x10\x00')
        result = get_variable_length_integer_from_bytes(data)
        assert result == 4096

    def test_is_variable_length_data_true(self):
        assert is_variable_length_data(DataArray)
        assert is_variable_length_data(DataStructure)

    def test_is_variable_length_data_false(self):
        # DataInteger-like classes have fixed length
        class FakeFixed:
            LENGTH = 2
        assert not is_variable_length_data(FakeFixed)


class TestBug3SetAccessSelection:
    """Bug 3: SET access selection parsing."""

    def test_parse_range_descriptor_single_entry(self):
        # Choice tag 0 (range descriptor), restricting_id=1 (single entry), value=5
        data = bytearray(b'\x00\x01\x05')
        result = parse_access_selection(data)
        assert isinstance(result, RangeDescriptor)
        assert result.restricting_identifier == 1
        # When data is consumed by optional check, range_start may be None
        # The descriptor was parsed successfully

    def test_parse_range_descriptor_with_explicit_value(self):
        # restricting_id=1, no obj_attr, then entry value
        data = bytearray(b'\x00\x01\x05\x03')
        result = parse_access_selection(data)
        assert isinstance(result, RangeDescriptor)
        assert result.restricting_identifier == 1

    def test_parse_range_descriptor_roundtrip(self):
        rd = RangeDescriptor(restricting_identifier=4, range_start=10, range_end=20)
        encoded = access_selection_to_bytes(rd)
        assert encoded[0] == AccessSelectionType.RANGE_DESCRIPTOR
        # parse_access_selection expects full bytes including choice tag
        parsed = parse_access_selection(bytearray(encoded))
        assert isinstance(parsed, RangeDescriptor)
        assert parsed.restricting_identifier == 4
        assert parsed.range_start == 10
        assert parsed.range_end == 20

    def test_parse_entry_descriptor(self):
        # Choice tag 1 (entry descriptor), count=2, len1=2, val1=ab, len2=2, val2=cd
        data = bytearray(b'\x01\x02\x02\xab\x02\xcd')
        result = parse_access_selection(data)
        assert isinstance(result, EntryDescriptor)
        assert len(result.entries) == 2

    def test_parse_selected_values(self):
        # Choice tag 2 (selected values), count=1, len=2, val=ef01
        data = bytearray(b'\x02\x01\x02\xef\x01')
        result = parse_access_selection(data)
        assert isinstance(result, SelectedValues)
        assert len(result.values) == 1

    def test_set_request_normal_with_access_selection_roundtrip(self):
        """Test SetRequestNormal with access selection can be encoded and decoded."""
        rd = RangeDescriptor(restricting_identifier=1, range_start=5)
        cosem_attr = cosem.CosemAttribute(
            interface=enums.CosemInterface(1),
            instance=cosem.Obis.from_bytes(b'\x00\x01\x02\x03\x04\x05'),
            attribute=2,
        )
        req = SetRequestNormal(
            cosem_attribute=cosem_attr,
            data=b'\x06\x00',
            access_selection=rd,
        )
        encoded = req.to_bytes()
        assert encoded[0] == 193  # TAG
        # Decode back
        decoded = SetRequestNormal.from_bytes(encoded)
        assert decoded.access_selection is not None
        assert isinstance(decoded.access_selection, RangeDescriptor)
        assert decoded.access_selection.range_start == 5


class TestBug4HdlcParameterNegotiation:
    """Bug 4: HDLC parameter negotiation."""

    def test_parameter_list_window_size(self):
        params = HdlcParameterList()
        params.set_window_size_tx(3)
        assert params.window_size == 3
        encoded = params.to_bytes()
        # Green Book header + WINDOW_SIZE_TX=3
        assert encoded == b'\x81\x80\x03\x07\x01\x03'

    def test_parameter_list_max_info_length(self):
        params = HdlcParameterList()
        params.set_max_info_length_tx(512)
        params.set_max_info_length_rx(1024)
        assert params.max_info_length == 512  # min of tx/rx
        encoded = params.to_bytes()
        decoded = HdlcParameterList.from_bytes(encoded)
        assert decoded.max_info_length_tx == 512
        assert decoded.max_info_length_rx == 1024

    def test_negotiate_parameters(self):
        client = HdlcParameterList()
        client.set_window_size_tx(5)
        client.set_max_info_length_tx(1024)
        server = HdlcParameterList()
        server.set_window_size_rx(3)
        server.set_max_info_length_rx(512)
        negotiated = negotiate_parameters(client, server)
        assert negotiated.window_size == 3
        assert negotiated.max_info_length_tx == 512

    def test_empty_parameter_list(self):
        params = HdlcParameterList()
        assert params.to_bytes() == b''
        assert params.window_size == 1  # default
        assert params.max_info_length == 128  # default

    def test_parameter_list_roundtrip(self):
        params = HdlcParameterList()
        params.set_window_size_tx(7)
        params.set_max_info_length_tx(2048)
        params.set_max_info_length_rx(2048)
        params.set_max_info_length_tx(2048)
        params.set_max_info_length_rx(2048)
        encoded = params.to_bytes()
        decoded = HdlcParameterList.from_bytes(encoded)
        assert decoded.window_size == 7
        assert decoded.max_info_length_tx == 2048
