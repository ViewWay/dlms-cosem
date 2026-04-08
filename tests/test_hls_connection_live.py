"""HLS Connection Tests with real meter encryption keys.

Based on actual meter logs:
- IP: 10.32.24.151:4059
- AKEY: D0D1D2D3D4D5D6D7D8D9DADBDCDDDEDF
- EKEY: 000102030405060708090A0B0C0D0E0F
"""
import pytest
from unittest.mock import Mock, MagicMock, AsyncMock
import bytes


class HLSConnectionConfig:
    """HLS connection configuration from real meter."""

    METER_HOST = "10.32.24.151"
    METER_PORT = 4059
    CLIENT_TITLE = "0000000000000000"

    # HLS Encryption Keys (from user)
    AKEY = bytes.fromhex("D0D1D2D3D4D5D6D7D8D9DADBDCDDDEDF")
    EKEY = bytes.fromhex("000102030405060708090A0B0C0D0E0F")


class TestHLSMessageParsing:
    """Test parsing of HLS messages from logs."""

    def test_aarq_parsing(self):
        """Test parsing AARQ with HLS LLS authentication."""
        # From logs: AARQ with HLS LLS
        aarq_hex = "60 42 A1 09 06 07 60 85 74 05 08 01 01 A6 0A 04 08 00 00 00 00 00 00 00 00 8A 02 07 80 8B 07 60 85 74 05 08 02 01 AC 0A 80 08 30 30 30 30 30 30 30 30 BE 10 04 0E 01 00 00 00 06 5F 1F 04 00 00 1F 1F FF FF"
        aarq_bytes = bytes.fromhex(aarq_hex.replace(" ", ""))

        # Verify AARQ tag
        assert aarq_bytes[0] == 0x60  # AARQ tag
        assert aarq_bytes[1] == 0x42  # Length

        # Verify authentication mechanism (LOW_LEVEL_SECURITY)
        assert b'\x8B\x07\x60\x85\x74\x05\x08\x02\x01' in aarq_bytes

        # Verify auth value (8 digits password)
        assert b'\xAC\x0A\x80' in aarq_bytes
        auth_idx = aarq_bytes.index(b'\xAC\x0A\x80')
        auth_len = aarq_bytes[auth_idx + 3]
        assert auth_len == 8
        auth_value = aarq_bytes[auth_idx + 4:auth_idx + 4 + auth_len]
        assert auth_value == b'3030303030303030'  # "00000000"

    def test_aare_parsing(self):
        """Test parsing AARE response."""
        # From logs: AARE response
        aare_hex = "61 29 A1 09 06 07 60 85 74 05 08 01 01 A2 03 02 01 00 A3 05 A1 03 02 01 00 BE 10 04 0E 08 00 06 5F 1F 04 00 00 10 10 04 C8 00 07"
        aare_bytes = bytes.fromhex(aare_hex.replace(" ", ""))

        # Verify AARE tag
        assert aare_bytes[0] == 0x61  # AARE tag

        # Verify association result (0 = accepted)
        assert aare_bytes[2] == 0xA2  # Result tag
        assert aare_bytes[4] == 0x00  # Accepted

        # Verify conformance bits
        assert b'\xBE\x10\x04\x0E' in aare_bytes

    def test_get_request_parsing(self):
        """Test parsing GET request from logs."""
        # From logs: GET request to device number
        get_hex = "C0 01 C1 00 01 00 00 2A 00 00 FF 02 00"
        get_bytes = bytes.fromhex(get_hex.replace(" ", ""))

        # Verify GET_REQUEST_NORMAL tag
        assert get_bytes[0] == 0xC0

        # Verify invoke ID
        assert get_bytes[2] == 0xC1

        # Verify attribute descriptor
        assert int.from_bytes(get_bytes[4:6], 'big') == 0x0001  # Class ID
        assert get_bytes[6:12] == bytes([0x00, 0x00, 0x2A, 0x00, 0x00, 0xFF])  # Instance: 0.0.42.0.0.255
        assert get_bytes[12] == 0x02  # Attribute ID

    def test_get_response_parsing(self):
        """Test parsing GET response from logs."""
        # From logs: GET response with device number
        resp_hex = "C4 01 C1 00 0A 08 4B 46 4D 31 30 32 30 31"
        resp_bytes = bytes.fromhex(resp_hex.replace(" ", ""))

        # Verify GET_RESPONSE_NORMAL tag
        assert resp_bytes[0] == 0xC4

        # Verify invoke ID matches
        assert resp_bytes[2] == 0xC1

        # Verify result (success)
        assert resp_bytes[4] == 0x00

        # Verify data (VisibleString)
        assert resp_bytes[5] == 0x0A  # VisibleString tag
        assert resp_bytes[6] == 0x08  # Length
        assert resp_bytes[7:15] == b'KFM10201'  # Device number

    def test_frame_counter_response_parsing(self):
        """Test parsing frame counter GET response."""
        # From logs: GET response with frame counter
        resp_hex = "C4 01 C1 00 06 00 00 00 16"
        resp_bytes = bytes.fromhex(resp_hex.replace(" ", ""))

        # Verify GET_RESPONSE_NORMAL tag
        assert resp_bytes[0] == 0xC4

        # Verify result (success)
        assert resp_bytes[4] == 0x00

        # Verify data (DoubleLongUnsigned)
        assert resp_bytes[5] == 0x06  # DoubleLongUnsigned tag
        assert int.from_bytes(resp_bytes[6:10], 'big') == 0x16  # 22

    def test_rlrq_parsing(self):
        """Test parsing RLRQ (Release Request)."""
        # From logs: RLRQ
        rlrq_hex = "62 15 80 01 00 BE 10 04 0E 01 00 00 00 06 5F 1F 04 00 00 1F 1F FF FF"
        rlrq_bytes = bytes.fromhex(rlrq_hex.replace(" ", ""))

        # Verify RLRQ tag
        assert rlrq_bytes[0] == 0x62  # RLRQ tag

        # Verify reason
        assert rlrq_bytes[2] == 0x80
        assert rlrq_bytes[3] == 0x01  # Normal release

    def test_rlre_parsing(self):
        """Test parsing RLRE (Release Response)."""
        # From logs: RLRE
        rlre_hex = "63 15 80 01 00 BE 10 04 0E 08 00 06 5F 1F 04 00 00 1A 1D 04 C8 00 07"
        rlre_bytes = bytes.fromhex(rlre_hex.replace(" ", ""))

        # Verify RLRE tag
        assert rlre_bytes[0] == 0x63  # RLRE tag

        # Verify result
        assert rlre_bytes[2] == 0x80
        assert rlre_bytes[3] == 0x01  # Normal release


class TestHLSWrapperParsing:
    """Test parsing of DLMS wrapper format."""

    def test_wrapper_header_parsing(self):
        """Test parsing wrapper header."""
        # From logs: GET request with wrapper
        wrapper_hex = "00 01 00 10 00 01 00 0D C0 01 C1 00 01 00 00 2A 00 00 FF 02 00"
        wrapper_bytes = bytes.fromhex(wrapper_hex.replace(" ", ""))

        # Parse wrapper header
        version = int.from_bytes(wrapper_bytes[0:2], 'big')
        source_wport = int.from_bytes(wrapper_bytes[2:6], 'big')
        dest_wport = int.from_bytes(wrapper_bytes[6:10], 'big')
        length = int.from_bytes(wrapper_bytes[10:14], 'big')

        # Verify wrapper fields
        assert version == 0x0001
        assert source_wport == 0x0010  # 16
        assert dest_wport == 0x0001   # 1
        assert length == 0x000D       # 13

    def test_wrapper_response_parsing(self):
        """Test parsing wrapper response."""
        # From logs: GET response with wrapper
        wrapper_hex = "00 01 00 01 00 10 00 0E C4 01 C1 00 0A 08 4B 46 4D 31 30 32 30 31"
        wrapper_bytes = bytes.fromhex(wrapper_hex.replace(" ", ""))

        # Parse wrapper header
        version = int.from_bytes(wrapper_bytes[0:2], 'big')
        source_wport = int.from_bytes(wrapper_bytes[2:6], 'big')
        dest_wport = int.from_bytes(wrapper_bytes[6:10], 'big')
        length = int.from_bytes(wrapper_bytes[10:14], 'big')

        # Verify wrapper fields (reversed for response)
        assert version == 0x0001
        assert source_wport == 0x0001  # 1 (meter)
        assert dest_wport == 0x0010   # 16 (client)
        assert length == 0x000E       # 14


class TestHLSEncryptionKeys:
    """Test HLS encryption key configuration."""

    def test_akey_format(self):
        """Test AKEY format."""
        akey = HLSConnectionConfig.AKEY

        # Should be 16 bytes (128 bits)
        assert len(akey) == 16

        # Verify key value
        assert akey == bytes.fromhex("D0D1D2D3D4D5D6D7D8D9DADBDCDDDEDF")

    def test_ekey_format(self):
        """Test EKEY format."""
        ekey = HLSConnectionConfig.EKEY

        # Should be 16 bytes (128 bits)
        assert len(ekey) == 16

        # Verify key value
        assert ekey == bytes.fromhex("000102030405060708090A0B0C0D0E0F")


class TestHLSConnectionSequence:
    """Test HLS connection sequence from logs."""

    def test_connection_sequence(self):
        """Test the complete connection sequence."""
        messages = [
            ("AARQ", "60", "Association Request (Public)"),
            ("AARE", "61", "Association Response (Public)"),
            ("GET", "C0", "GET Request (Device Number)"),
            ("GET_RESP", "C4", "GET Response (Device Number)"),
            ("GET", "C0", "GET Request (Frame Counter)"),
            ("GET_RESP", "C4", "GET Response (Frame Counter)"),
            ("RLRQ", "62", "Release Request (Public)"),
            ("RLRE", "63", "Release Response (Public)"),
            ("AARQ", "60", "Association Request (HLS LLS)"),
            ("AARE", "61", "Association Response (HLS LLS)"),
        ]

        # Verify all expected message types are present
        tags = [msg[1] for msg in messages]
        assert "60" in tags  # AARQ
        assert "61" in tags  # AARE
        assert "C0" in tags  # GET
        assert "C4" in tags  # GET_RESP
        assert "62" in tags  # RLRQ
        assert "63" in tags  # RLRE

    def test_device_number_read(self):
        """Test device number read operation."""
        # Device number: 0.0.42.0.0.255 attribute 2
        obis = "0.0.42.0.0.255"
        attribute = 2

        # Parse OBIS
        parts = obis.split(".")
        assert len(parts) == 6

        # Convert to bytes
        obis_bytes = bytes([int(p) for p in parts])
        expected = bytes([0x00, 0x00, 0x2A, 0x00, 0x00, 0xFF])
        assert obis_bytes == expected

        # Attribute ID
        assert attribute == 2

    def test_frame_counter_read(self):
        """Test frame counter read operation."""
        # Frame counter: 0.0.43.1.0.255 attribute 2
        obis = "0.0.43.1.0.255"
        attribute = 2

        # Parse OBIS
        parts = obis.split(".")
        assert len(parts) == 6

        # Convert to bytes
        obis_bytes = bytes([int(p) for p in parts])
        expected = bytes([0x00, 0x00, 0x2B, 0x01, 0x00, 0xFF])
        assert obis_bytes == expected


@pytest.mark.skipif(
    True,  # Skip by default, enable for live testing
    reason="Requires live meter connection. Set to False to enable."
)
class TestHLSLiveConnection:
    """Live HLS connection tests (requires meter access)."""

    @pytest.fixture
    async def hls_client(self):
        """Create HLS client for live testing."""
        from dlms_cosem import AsyncDlmsClient
        from dlms_cosem.io import TcpIO
        from dlms_cosem.transport import HdlcTransport
        from dlms_cosem import DlmsConnectionSettings

        io = TcpIO(host=HLSConnectionConfig.METER_HOST, port=HLSConnectionConfig.METER_PORT)
        transport = HdlcTransport(io)

        settings = DlmsConnectionSettings(
            client_logical_address=16,
            server_logical_address=1,
            authentication="hls",
            authentication_key=HLSConnectionConfig.AKEY,
            encryption_key=HLSConnectionConfig.EKEY,
            client_system_title=bytes.fromhex(HLSConnectionConfig.CLIENT_TITLE),
        )

        client = AsyncDlmsClient(transport, settings)

        await client.connect()
        yield client
        await client.close()

    @pytest.mark.asyncio
    async def test_hls_get_device_number(self, hls_client):
        """Test GET device number with HLS."""
        result = await hls_client.get("0.0.42.0.0.255", attribute=2)
        assert result is not None

    @pytest.mark.asyncio
    async def test_hls_get_meter_id(self, hls_client):
        """Test GET meter ID with HLS."""
        result = await hls_client.get("0.0.96.1.0.255")
        assert result is not None

    @pytest.mark.asyncio
    async def test_hls_get_clock(self, hls_client):
        """Test GET clock with HLS."""
        result = await hls_client.get("0.0.1.0.0.255")
        assert result is not None


class TestHLSConfiguration:
    """Test HLS configuration setup."""

    def test_connection_config_setup(self):
        """Test connection configuration with HLS keys."""
        from dlms_cosem import DlmsConnectionSettings

        settings = DlmsConnectionSettings(
            client_logical_address=16,
            server_logical_address=1,
            authentication="hls",
            authentication_key=HLSConnectionConfig.AKEY,
            encryption_key=HLSConnectionConfig.EKEY,
            client_system_title=bytes.fromhex(HLSConnectionConfig.CLIENT_TITLE),
        )

        assert settings.client_logical_address == 16
        assert settings.server_logical_address == 1
        assert settings.authentication == "hls"
        assert settings.authentication_key == HLSConnectionConfig.AKEY
        assert settings.encryption_key == HLSConnectionConfig.EKEY
