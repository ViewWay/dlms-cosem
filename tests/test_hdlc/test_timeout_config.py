"""Tests for HDLC timeout/retry configuration (Green Book 8.4.5.6)."""

import pytest

from dlms_cosem.hdlc.parameters import HdlcTimeoutConfig
from dlms_cosem.hdlc.exceptions import HdlcTimeoutError
from dlms_cosem.hdlc.connection import HdlcConnection
from dlms_cosem.hdlc import address


class TestHdlcTimeoutConfigDefaults:
    def test_default_values(self):
        config = HdlcTimeoutConfig()
        assert config.to_wait_resp_ms == 5000
        assert config.max_nb_of_retries == 3
        assert config.inactivity_timeout_ms == 30000
        assert config.inter_frame_timeout_ms == 500

    def test_custom_values(self):
        config = HdlcTimeoutConfig(
            to_wait_resp_ms=3000,
            max_nb_of_retries=5,
            inactivity_timeout_ms=60000,
            inter_frame_timeout_ms=200,
        )
        assert config.to_wait_resp_ms == 3000
        assert config.max_nb_of_retries == 5
        assert config.inactivity_timeout_ms == 60000
        assert config.inter_frame_timeout_ms == 200

    def test_partial_custom(self):
        config = HdlcTimeoutConfig(to_wait_resp_ms=1000)
        assert config.to_wait_resp_ms == 1000
        assert config.max_nb_of_retries == 3  # default


class TestHdlcConnectionTimeoutIntegration:
    def test_connection_accepts_timeout_config(self):
        client = address.HdlcAddress(1, 16)
        server = address.HdlcAddress(1, 1)
        timeout = HdlcTimeoutConfig(to_wait_resp_ms=1000)
        conn = HdlcConnection(
            client_address=client,
            server_address=server,
            timeout_config=timeout,
        )
        assert conn.timeout_config.to_wait_resp_ms == 1000
        assert conn.timeout_config.max_nb_of_retries == 3

    def test_connection_default_timeout_config(self):
        client = address.HdlcAddress(1, 16)
        server = address.HdlcAddress(1, 1)
        conn = HdlcConnection(
            client_address=client,
            server_address=server,
        )
        assert conn.timeout_config.to_wait_resp_ms == 5000
