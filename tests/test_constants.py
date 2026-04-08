"""
Tests for DLMS/COSEM constants.
"""
from dlms_cosem.constants import DLMS_UDP_PORT, DLMS_TCP_PORT


def test_dlms_udp_port():
    """Test DLMS UDP port constant."""
    assert DLMS_UDP_PORT == 4059


def test_dlms_tcp_port():
    """Test DLMS TCP port constant."""
    assert DLMS_TCP_PORT == 4059
