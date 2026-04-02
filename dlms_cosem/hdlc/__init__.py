"""
HDLC layer implementation for DLMS/COSEM.

This module provides HDLC frame handling, parameter negotiation,
and address management for DLMS/COSEM communication.
"""

# Frame types
from dlms_cosem.hdlc.frames import (
    BaseHdlcFrame,
    DisconnectFrame,
    InformationFrame,
    ReceiveReadyFrame,
    SetNormalResponseModeFrame,
    UnNumberedAcknowledgmentFrame,
    UnnumberedInformationFrame,
    frame_has_correct_length,
    frame_is_enclosed_by_hdlc_flags,
)

# Address handling
from dlms_cosem.hdlc.address import HdlcAddress

# Parameter negotiation
from dlms_cosem.hdlc.parameters import (
    DEFAULT_MAX_INFO_LENGTH,
    DEFAULT_WINDOW_SIZE,
    HdlcParameter,
    HdlcParameterList,
    HdlcParameterRange,
    HdlcParameterType,
    PARAMETER_RANGES,
    negotiate_parameters,
)

# Window control for multi-frame transmission
from dlms_cosem.hdlc.window import (
    SlidingWindow,
    FrameBuffer,
    FrameInfo,
    WindowState,
)

# Segmentation support
from dlms_cosem.hdlc.segmentation import (
    SegmentedFrameInfo,
    SegmentedFrameReassembler,
    split_information_into_segments,
    create_segmented_i_frames,
)

# Exceptions
from dlms_cosem.hdlc import exceptions as hdlc_exceptions

__all__ = [
    # Frames
    "BaseHdlcFrame",
    "SetNormalResponseModeFrame",
    "UnNumberedAcknowledgmentFrame",
    "InformationFrame",
    "ReceiveReadyFrame",
    "DisconnectFrame",
    "UnnumberedInformationFrame",
    "frame_is_enclosed_by_hdlc_flags",
    "frame_has_correct_length",
    # Address
    "HdlcAddress",
    # Parameters
    "HdlcParameter",
    "HdlcParameterList",
    "HdlcParameterType",
    "HdlcParameterRange",
    "PARAMETER_RANGES",
    "DEFAULT_WINDOW_SIZE",
    "DEFAULT_MAX_INFO_LENGTH",
    "negotiate_parameters",
    # Window control
    "SlidingWindow",
    "FrameBuffer",
    "FrameInfo",
    "WindowState",
    # Segmentation
    "SegmentedFrameInfo",
    "SegmentedFrameReassembler",
    "split_information_into_segments",
    "create_segmented_i_frames",
    # Exceptions
    "hdlc_exceptions",
]
