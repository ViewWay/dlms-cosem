"""Gateway frame module for DLMS/COSEM.

This module implements the Gateway Frame format used for GPRS/3G/4G routing.
The gateway frame wraps DLMS PDU with network routing information including
network ID and physical device address.

Reference: pdlms/pdlms/protocol/frame/gateway/GatewayFrame.py
"""

from dlms_cosem.protocol.frame.gateway.gateway_frame import GatewayFrame

__all__ = ["GatewayFrame"]
