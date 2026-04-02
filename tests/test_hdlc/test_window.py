"""
Tests for HDLC sliding window control module.
"""
import pytest

from dlms_cosem.hdlc.window import (
    SlidingWindow,
    FrameBuffer,
    FrameInfo,
    WindowState,
)


class TestSlidingWindow:
    """Tests for the SlidingWindow class."""

    def test_init_default_window_size(self):
        """Test initialization with default window size."""
        window = SlidingWindow()
        assert window.window_size == 1
        assert window.base_sequence == 0
        assert window.next_sequence == 0
        assert window.receive_sequence == 0
        assert window.state == WindowState.READY

    def test_init_custom_window_size(self):
        """Test initialization with custom window size."""
        window = SlidingWindow(window_size=5)
        assert window.window_size == 5
        assert len(window.frames) == 5

    def test_init_invalid_window_size_too_low(self):
        """Test that window size must be at least 1."""
        with pytest.raises(ValueError, match="Window size must be 1-7"):
            SlidingWindow(window_size=0)

    def test_init_invalid_window_size_too_high(self):
        """Test that window size must be at most 7."""
        with pytest.raises(ValueError, match="Window size must be 1-7"):
            SlidingWindow(window_size=8)

    def test_available_slots_initially(self):
        """Test that all slots are available initially."""
        window = SlidingWindow(window_size=4)
        assert window.available_slots == 4

    def test_available_slots_after_adding_frame(self):
        """Test that available slots decrease after adding frames."""
        window = SlidingWindow(window_size=3)
        window.add_frame(0, b"data1")
        assert window.available_slots == 2

    def test_window_used_property(self):
        """Test the window_used property."""
        window = SlidingWindow(window_size=3)
        assert window.window_used == 0
        window.add_frame(0, b"data1")
        assert window.window_used == 1

    def test_can_send_when_ready(self):
        """Test can_send returns True when window is ready."""
        window = SlidingWindow()
        assert window.can_send() is True

    def test_cannot_send_when_window_full(self):
        """Test that frames cannot be sent when window is full."""
        window = SlidingWindow(window_size=1)
        window.add_frame(0, b"data1")
        # Window is now full (size=1, one frame added)
        assert window.available_slots == 0
        assert window.can_send() is False

    def test_add_frame_increments_sequence(self):
        """Test that adding a frame increments next_sequence."""
        window = SlidingWindow()
        window.add_frame(0, b"data1")
        assert window.next_sequence == 1

    def test_add_frame_sequence_wraps_at_8(self):
        """Test that sequence numbers wrap from 7 to 0."""
        window = SlidingWindow()
        window.add_frame(7, b"data1")
        assert window.next_sequence == 0

    def test_add_frame_invalid_sequence_number(self):
        """Test that invalid sequence numbers are rejected."""
        window = SlidingWindow()
        with pytest.raises(ValueError, match="Sequence number must be 0-7"):
            window.add_frame(8, b"data")

    def test_add_frame_duplicate_sequence(self):
        """Test that duplicate sequence numbers are rejected."""
        window = SlidingWindow(window_size=3)
        window.add_frame(0, b"data1")
        with pytest.raises(ValueError, match="is already occupied"):
            window.add_frame(0, b"data2")

    def test_add_frame_when_window_full(self):
        """Test that frames cannot be added when window is full."""
        window = SlidingWindow(window_size=1)
        window.add_frame(0, b"data1")
        with pytest.raises(ValueError, match="Cannot send frame"):
            window.add_frame(1, b"data2")

    def test_get_frame_to_transmit(self):
        """Test getting the next frame to transmit."""
        window = SlidingWindow()
        window.add_frame(0, b"data1")
        frame = window.get_frame_to_transmit()
        assert frame == (0, b"data1")

    def test_get_frame_to_transmit_returns_none_when_empty(self):
        """Test that get_frame_to_transmit returns None when no frames."""
        window = SlidingWindow()
        assert window.get_frame_to_transmit() is None

    def test_mark_transmitted(self):
        """Test marking a frame as transmitted."""
        window = SlidingWindow()
        window.add_frame(0, b"data1")
        window.mark_transmitted(0)
        frame = window.get_frame_to_transmit()
        # Should return None since frame is already transmitted
        assert frame is None

    def test_acknowledge_received_single_frame(self):
        """Test acknowledging a single frame."""
        window = SlidingWindow()
        window.add_frame(0, b"data1")
        window.mark_transmitted(0)

        acknowledged = window.acknowledge_received(1)
        assert acknowledged == [0]

    def test_acknowledge_received_multiple_frames(self):
        """Test acknowledging multiple frames at once."""
        window = SlidingWindow(window_size=3)
        window.add_frame(0, b"data1")
        window.add_frame(1, b"data2")
        window.add_frame(2, b"data3")
        for i in range(3):
            window.mark_transmitted(i)

        # Acknowledge all three frames
        acknowledged = window.acknowledge_received(3)
        assert len(acknowledged) == 3
        assert 0 in acknowledged
        assert 1 in acknowledged
        assert 2 in acknowledged

    def test_acknowledge_with_wraparound(self):
        """Test acknowledgment with sequence wraparound."""
        window = SlidingWindow(window_size=4)
        # Add frames with sequences 6, 7, 0
        window.add_frame(6, b"data6")
        window.add_frame(7, b"data7")
        window.base_sequence = 6  # Simulate we're at sequence 6
        window.add_frame(0, b"data0")

        for seq in [6, 7, 0]:
            window.mark_transmitted(seq)

        # Acknowledge up to sequence 1 (which acknowledges 6, 7, 0)
        acknowledged = window.acknowledge_received(1)
        assert 6 in acknowledged or len(acknowledged) > 0

    def test_get_unacknowledged_frames(self):
        """Test getting unacknowledged frames."""
        window = SlidingWindow(window_size=3)
        window.add_frame(0, b"data1")
        window.add_frame(1, b"data2")

        # Mark first as transmitted but not acknowledged
        window.mark_transmitted(0)
        window.mark_transmitted(1)

        unacked = window.get_unacknowledged_frames()
        assert len(unacked) == 2
        assert (0, b"data1") in unacked
        assert (1, b"data2") in unacked

    def test_get_unacknowledged_excludes_acknowledged(self):
        """Test that acknowledged frames are not in unacknowledged list."""
        window = SlidingWindow()
        window.add_frame(0, b"data1")
        window.mark_transmitted(0)
        window.acknowledge_received(1)

        unacked = window.get_unacknowledged_frames()
        assert len(unacked) == 0

    def test_reset_clears_state(self):
        """Test that reset clears all state."""
        window = SlidingWindow(window_size=3)
        window.add_frame(0, b"data1")
        window.mark_transmitted(0)
        window.acknowledge_received(1)
        window.state = WindowState.WAITING_ACK

        window.reset()

        assert window.base_sequence == 0
        assert window.next_sequence == 0
        assert window.receive_sequence == 0
        assert window.state == WindowState.READY
        assert window.window_used == 0

    def test_sliding_window_forward(self):
        """Test that the window slides forward after acknowledgment."""
        window = SlidingWindow(window_size=3)

        # Add frames 0, 1, 2
        for i in range(3):
            window.add_frame(i, f"data{i}".encode())
            window.mark_transmitted(i)

        # Acknowledge frame 0
        window.acknowledge_received(1)

        # Base should move to 1, freeing slot for new frame
        assert window.base_sequence == 1
        assert window.available_slots == 1  # One slot freed

    def test_count_unacknowledged(self):
        """Test counting unacknowledged frames."""
        window = SlidingWindow(window_size=3)
        assert window.count_unacknowledged() == 0

        window.add_frame(0, b"data1")
        window.mark_transmitted(0)
        assert window.count_unacknowledged() == 1

        window.acknowledge_received(1)
        assert window.count_unacknowledged() == 0


class TestFrameBuffer:
    """Tests for the FrameBuffer class."""

    def test_init(self):
        """Test FrameBuffer initialization."""
        buffer = FrameBuffer()
        assert buffer.max_size == 256
        assert buffer.next_expected == 0
        assert buffer.buffered_count == 0

    def test_init_custom_max_size(self):
        """Test FrameBuffer with custom max size."""
        buffer = FrameBuffer(max_size=10)
        assert buffer.max_size == 10

    def test_add_frame(self):
        """Test adding a frame to the buffer."""
        buffer = FrameBuffer()
        result = buffer.add_frame(0, b"data1")
        assert result is True
        assert buffer.buffered_count == 1
        assert buffer.has_frame(0)

    def test_add_duplicate_frame(self):
        """Test that duplicate frames are rejected."""
        buffer = FrameBuffer()
        buffer.add_frame(0, b"data1")
        result = buffer.add_frame(0, b"data2")
        assert result is False
        assert buffer.buffered_count == 1

    def test_add_frame_when_full(self):
        """Test that frames are rejected when buffer is full."""
        buffer = FrameBuffer(max_size=2)
        buffer.add_frame(0, b"data1")
        buffer.add_frame(1, b"data2")
        result = buffer.add_frame(2, b"data3")
        assert result is False

    def test_get_deliverable_frames_in_order(self):
        """Test getting deliverable frames in sequence order."""
        buffer = FrameBuffer()
        buffer.add_frame(1, b"data2")
        buffer.add_frame(0, b"data1")
        buffer.add_frame(2, b"data3")

        deliverable = buffer.get_deliverable_frames()
        assert len(deliverable) == 3
        assert deliverable[0] == (0, b"data1")
        assert deliverable[1] == (1, b"data2")
        assert deliverable[2] == (2, b"data3")

    def test_get_deliverable_frames_with_gap(self):
        """Test that frames before a gap are delivered."""
        buffer = FrameBuffer()
        buffer.add_frame(0, b"data1")
        buffer.add_frame(2, b"data3")  # Gap: frame 1 is missing

        deliverable = buffer.get_deliverable_frames()
        assert len(deliverable) == 1
        assert deliverable[0] == (0, b"data1")
        assert buffer.next_expected == 1

    def test_get_deliverable_frames_returns_empty(self):
        """Test get_deliverable_frames when no frames available."""
        buffer = FrameBuffer()
        deliverable = buffer.get_deliverable_frames()
        assert len(deliverable) == 0

    def test_get_deliverable_clears_buffer(self):
        """Test that delivered frames are removed from buffer."""
        buffer = FrameBuffer()
        buffer.add_frame(0, b"data1")
        buffer.add_frame(1, b"data2")

        buffer.get_deliverable_frames()
        assert buffer.buffered_count == 0

    def test_has_frame(self):
        """Test has_frame method."""
        buffer = FrameBuffer()
        assert buffer.has_frame(0) is False

        buffer.add_frame(0, b"data1")
        assert buffer.has_frame(0) is True

    def test_clear(self):
        """Test clearing the buffer."""
        buffer = FrameBuffer()
        buffer.add_frame(0, b"data1")
        buffer.add_frame(1, b"data2")

        buffer.clear()
        assert buffer.buffered_count == 0
        assert buffer.next_expected == 0

    def test_next_expected_updates(self):
        """Test that next_expected is updated after delivery."""
        buffer = FrameBuffer()
        buffer.add_frame(0, b"data1")
        buffer.add_frame(1, b"data2")

        buffer.get_deliverable_frames()
        assert buffer.next_expected == 2


class TestFrameInfo:
    """Tests for the FrameInfo dataclass."""

    def test_create_frame_info(self):
        """Test creating a FrameInfo instance."""
        info = FrameInfo(sequence_number=3, data=b"test")
        assert info.sequence_number == 3
        assert info.data == b"test"
        assert info.acknowledged is False
        assert info.transmitted is False
        assert info.retransmit_count == 0

    def test_frame_info_defaults(self):
        """Test FrameInfo default values."""
        info = FrameInfo(sequence_number=0, data=b"data")
        assert info.acknowledged is False
        assert info.transmitted is False
        assert info.retransmit_count == 0

    def test_frame_info_with_acknowledged(self):
        """Test FrameInfo with acknowledged set."""
        info = FrameInfo(sequence_number=0, data=b"data", acknowledged=True)
        assert info.acknowledged is True

    def test_frame_info_with_transmitted(self):
        """Test FrameInfo with transmitted set."""
        info = FrameInfo(sequence_number=0, data=b"data", transmitted=True)
        assert info.transmitted is True

    def test_frame_info_with_retransmit_count(self):
        """Test FrameInfo with retransmit count."""
        info = FrameInfo(sequence_number=0, data=b"data", retransmit_count=3)
        assert info.retransmit_count == 3
