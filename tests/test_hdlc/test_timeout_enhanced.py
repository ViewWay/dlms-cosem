"""Enhanced timeout config edge case tests."""

import pytest

from dlms_cosem.hdlc.parameters import HdlcTimeoutConfig
from dlms_cosem.hdlc.connection import HdlcConnection
from dlms_cosem.hdlc import address


class TestTimeoutBoundary:
    """Timeout config boundary values."""

    def test_zero_timeout(self):
        config = HdlcTimeoutConfig(to_wait_resp_ms=0)
        assert config.to_wait_resp_ms == 0

    def test_large_timeout(self):
        config = HdlcTimeoutConfig(inactivity_timeout_ms=3600000)
        assert config.inactivity_timeout_ms == 3600000

    def test_zero_retries(self):
        config = HdlcTimeoutConfig(max_nb_of_retries=0)
        assert config.max_nb_of_retries == 0

    def test_max_retries(self):
        config = HdlcTimeoutConfig(max_nb_of_retries=255)
        assert config.max_nb_of_retries == 255

    def test_zero_inter_frame_timeout(self):
        config = HdlcTimeoutConfig(inter_frame_timeout_ms=0)
        assert config.inter_frame_timeout_ms == 0


class TestTimeoutConnectionIntegration:
    """Timeout config with connection."""

    def test_connection_with_minimal_timeout(self):
        c = address.HdlcAddress(1, None, "client")
        s = address.HdlcAddress(1, None, "server")
        config = HdlcTimeoutConfig(to_wait_resp_ms=100, max_nb_of_retries=1)
        conn = HdlcConnection(client_address=c, server_address=s, timeout_config=config)
        assert conn.timeout_config.to_wait_resp_ms == 100
        assert conn.timeout_config.max_nb_of_retries == 1

    def test_connection_with_zero_retries(self):
        c = address.HdlcAddress(1, None, "client")
        s = address.HdlcAddress(1, None, "server")
        config = HdlcTimeoutConfig(max_nb_of_retries=0)
        conn = HdlcConnection(client_address=c, server_address=s, timeout_config=config)
        assert conn.timeout_config.max_nb_of_retries == 0
