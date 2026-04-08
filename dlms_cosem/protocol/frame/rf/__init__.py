"""RF (Radio Frequency) frame module for DLMS/COSEM.

This module implements the RF Frame format used for wireless communication
with meters using ISM band radio (e.g., 470MHz in China).

Reference: pdlms/pdlms/protocol/frame/rf/RFFrame.py
"""

from dlms_cosem.protocol.frame.rf.rf_frame import RFFrame

__all__ = ["RFFrame"]
