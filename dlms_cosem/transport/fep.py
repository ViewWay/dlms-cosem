"""FEP (Front End Processor) transport for DLMS/COSEM.

FEP is a common protocol used in Chinese power grid for meter data collection.
The FEP acts as a gateway between the central system and meters, using a
proprietary frame format.

Frame format:
    Fixed header (10B) + Length (2B LE) + Command (2B) + Logical address (32B)
    + DLMS APDU + Checksum (1B) + 0x16

DLMS APDU within FEP:
    0001 + srcWPort (4B) + dstWPort (4B) + length (4B) + [gateway header] + user info (APDU)

Reference: pdlms.protocol.fep, pdlms.protocol.frame.fep.FepFrame
"""
from typing import Optional

import structlog

from dlms_cosem.io import IoImplementation

LOG = structlog.get_logger()

# Frame markers
FEP_START_BYTE = 0x68
FEP_END_BYTE = 0x16

# Command codes
FEP_CMD_DATA_TRANSFER = 0x407A
FEP_CMD_CONNECT = 0xA103
FEP_CMD_DISCONNECT = 0xA200
FEP_CMD_GET_DEVICES = 0x2C02

# Header offsets
FEP_HEADER_LEN = 10
FEP_LENGTH_OFFSET = 9
FEP_LENGTH_BYTES = 2
FEP_TAIL_LEN = 2  # checksum + end byte
FEP_LOGICAL_ADDR_LEN = 32

# WPDU header within FEP DLMS APDU
WPDU_HEADER_LEN = 8  # 0001 + srcWPort(4) + dstWPort(4) + len(4) → but first 4 bytes are tag


def fep_checksum(data: bytes) -> int:
    """Calculate FEP frame checksum (sum of all bytes mod 256).

    Args:
        data: Raw bytes to checksum (excluding checksum and end byte).

    Returns:
        Checksum value (0-255).
    """
    return sum(data) % 256


def _int_to_hex_bytes(value: int, byte_length: int) -> str:
    """Convert integer to zero-padded hex string (no spaces).

    Args:
        value: Integer value.
        byte_length: Number of bytes (e.g., 2 → 4 hex chars).

    Returns:
        Hex string without spaces or prefix.
    """
    return format(value, f'0{byte_length * 2}X')


def build_fep_connect_pdu(mst_addr: int, password: str) -> bytes:
    """Build FEP connect PDU.

    Frame: 68 82 40 [addr 2B] 00 20 00 68 A1 03 00 [pass] [checksum] 16

    Args:
        mst_addr: FEP master station address (2 bytes).
        password: FEP master station password (hex string, e.g. "314156").

    Returns:
        Complete connect PDU bytes.
    """
    addr_hex = _int_to_hex_bytes(mst_addr, 2)
    body = bytes.fromhex(f"688240{addr_hex}00200068A10300{password}")
    cs = fep_checksum(body)
    return body + bytes([cs, FEP_END_BYTE])


def build_fep_disconnect_pdu(mst_addr: int) -> bytes:
    """Build FEP disconnect PDU.

    Args:
        mst_addr: FEP master station address.

    Returns:
        Complete disconnect PDU bytes.
    """
    addr_hex = _int_to_hex_bytes(mst_addr, 2)
    body = bytes.fromhex(f"688240{addr_hex}00200068A20000")
    cs = fep_checksum(body)
    return body + bytes([cs, FEP_END_BYTE])


def build_fep_get_devices_pdu(mst_addr: int) -> bytes:
    """Build FEP get device list PDU.

    Args:
        mst_addr: FEP master station address.

    Returns:
        Complete get-devices PDU bytes.
    """
    addr_hex = _int_to_hex_bytes(mst_addr, 2)
    body = bytes.fromhex(f"688240{addr_hex}002000682C0200227A")
    cs = fep_checksum(body)
    return body + bytes([cs, FEP_END_BYTE])


def encode_fep_frame(
    mst_addr: int,
    meter_no: str,
    apdu: bytes,
    src_wport: int,
    dst_wport: int,
    use_gateway: bool = False,
) -> bytes:
    """Encode APDU into FEP frame.

    Args:
        mst_addr: FEP master station address.
        meter_no: Meter number (logical address, ASCII string).
        apdu: Raw DLMS APDU bytes.
        src_wport: Source W-Port (client).
        dst_wport: Destination W-Port (server).
        use_gateway: If True, include E6 gateway header in DLMS APDU.

    Returns:
        Complete FEP frame bytes.
    """
    addr_hex = _int_to_hex_bytes(mst_addr, 2)
    header = bytes.fromhex(f"680000{addr_hex}002000682A")

    cmd = FEP_CMD_DATA_TRANSFER
    logical_addr = meter_no.encode('ascii').ljust(FEP_LOGICAL_ADDR_LEN, b'\x00')

    # Build DLMS APDU section
    apdu_hex = apdu.hex().upper()
    if use_gateway:
        meter_hex = meter_no.encode('ascii').hex().upper()
        addr_len_hex = _int_to_hex_bytes(len(meter_no), 2)
        gateway_hex = f"E600{addr_len_hex}{meter_hex}"
        dlms_apdu_len = (len(apdu_hex) + len(gateway_hex)) // 2
        dlms_apdu_hex = (
            f"0001"
            f"{_int_to_hex_bytes(src_wport, 4)}"
            f"{_int_to_hex_bytes(dst_wport, 4)}"
            f"{_int_to_hex_bytes(dlms_apdu_len, 4)}"
            f"{gateway_hex}"
            f"{apdu_hex}"
        )
    else:
        apdu_byte_len = len(apdu)
        dlms_apdu_hex = (
            f"0001"
            f"{_int_to_hex_bytes(src_wport, 4)}"
            f"{_int_to_hex_bytes(dst_wport, 4)}"
            f"{_int_to_hex_bytes(apdu_byte_len, 4)}"
            f"{apdu_hex}"
        )

    payload = cmd.to_bytes(2, 'big') + logical_addr + bytes.fromhex(dlms_apdu_hex)
    payload_len = len(payload)

    # Length field: 2 bytes, little-endian
    length_le = payload_len.to_bytes(2, 'little')

    frame_without_cs = header + length_le + payload
    cs = fep_checksum(frame_without_cs)

    return frame_without_cs + bytes([cs, FEP_END_BYTE])


def fep_frame_payload_length(raw: bytes) -> int:
    """Calculate total FEP frame length from header.

    Frame layout: header(10) + length_le(2) + payload + checksum(1) + end(1)
    Length field at bytes 9-10 (little-endian) = payload length.
    Total = 10 + 2 + payload_length + 1 + 1 = 14 + payload_length.

    Args:
        raw: At least 12 bytes of frame data.

    Returns:
        Total frame length in bytes. Returns 0 if raw is too short.
    """
    if len(raw) < 12:
        return 0
    payload_len = int.from_bytes(raw[10:12], 'little')
    return 12 + payload_len + 2  # header(10)+len(2)+payload+cs(1)+end(1)


def parse_fep_response(raw: bytes, strip_gateway: bool = False) -> bytes:
    """Parse APDU from FEP response frame.

    Strip FEP header (45 bytes) and tail (2 bytes), then extract
    DLMS APDU from WPDU wrapper.

    Args:
        raw: Complete FEP response bytes.
        strip_gateway: If True, remove E7 gateway header from APDU.

    Returns:
        Extracted APDU bytes.
    """
    # Frame layout: header(10) + len_le(2) + cmd(2) + logical_addr(32) + wpdu(N) + user_info + cs(1) + end(1)
    # DLMS APDU region starts at byte 12 (after header+length)
    # Skip cmd(2) + addr(32) + wpdu(14) = 48 bytes to reach user_info
    FEP_RESP_HEADER_LEN = 12 + 2 + 32  # = 46
    FEP_RESP_TAIL_LEN = 2
    WPDU_HDR_LEN = 14  # 0001(2) + src(4) + dst(4) + len(4)

    if len(raw) < FEP_RESP_HEADER_LEN + WPDU_HDR_LEN + FEP_RESP_TAIL_LEN:
        return raw

    body = raw[FEP_RESP_HEADER_LEN:-FEP_RESP_TAIL_LEN]

    if len(body) <= WPDU_HDR_LEN:
        return b""

    user_info = body[WPDU_HDR_LEN:]

    if strip_gateway and len(user_info) >= 4 and user_info[0] == 0xE7:
        # E7 gateway: E7(1) + netId(1) + addrLen(1) + addr(addrLen) + ...
        # Note: the WPDU length field counts gateway+apdu bytes,
        # but we just skip 3 + addrLen to get past the gateway header
        if len(user_info) < 3:
            return user_info
        addr_len = user_info[2]
        if len(user_info) >= 3 + addr_len:
            user_info = user_info[3 + addr_len:]

    return user_info


def parse_get_devices_response(raw: bytes) -> list:
    """Parse device list from FEP get-devices response.

    Each device entry is 100 hex chars (50 bytes), with meter number
    in the first 64 hex chars (32 bytes, ASCII, zero-padded).

    Args:
        raw: Complete FEP response bytes.

    Returns:
        List of meter number strings.

    Raises:
        ValueError: If response format is invalid.
    """
    devices = []

    # Strip fixed header and tail
    if len(raw) < 42:
        return devices

    data = raw[38:-4]
    data_hex = data.hex().upper()

    if len(data_hex) % 100 != 0:
        raise ValueError(
            f"Invalid FEP device list response: "
            f"data length {len(data_hex)} not multiple of 100"
        )

    for i in range(0, len(data_hex), 100):
        meter_hex = data_hex[i:i + 64].rstrip('0')
        if len(meter_hex) % 2 != 0:
            meter_hex += '0'
        try:
            meter_no = bytes.fromhex(meter_hex).decode('ascii').rstrip('\x00')
            devices.append(meter_no)
        except (ValueError, UnicodeDecodeError):
            LOG.warning("Failed to decode meter number", hex=meter_hex)

    return devices


class FepTransport(IoImplementation):
    """FEP transport implementation for DLMS/COSEM.

    Wraps a TCP connection with FEP frame encoding/decoding.

    Usage::

        transport = FepTransport(mst_addr=5, meter_no="000000000001")
        await transport.connect("192.168.1.1", 8000)
        apdu = transport.encode_apdu(dlms_apdu_bytes)
        transport.write(apdu)
        response = transport.read()
    """

    def __init__(
        self,
        mst_addr: int,
        meter_no: str,
        src_wport: int = 1,
        dst_wport: int = 1,
        use_gateway: bool = False,
        timeout: float = 10.0,
    ) -> None:
        """Initialize FEP transport.

        Args:
            mst_addr: FEP master station address.
            meter_no: Meter number (logical address).
            src_wport: Source W-Port.
            dst_wport: Destination W-Port.
            use_gateway: Use gateway header in frames.
            timeout: Connection/IO timeout in seconds.
        """
        self.mst_addr = mst_addr
        self.meter_no = meter_no
        self.src_wport = src_wport
        self.dst_wport = dst_wport
        self.use_gateway = use_gateway
        self.timeout = timeout
        self._inner: Optional[IoImplementation] = None

    @property
    def inner(self) -> Optional[IoImplementation]:
        """Underlying IO implementation."""
        return self._inner

    @inner.setter
    def inner(self, value: IoImplementation) -> None:
        self._inner = value

    def connect(self, io: IoImplementation) -> None:
        """Connect to FEP server.

        Sends FEP connect PDU and verifies response.

        Args:
            io: Underlying IO implementation (e.g., TCP).

        Raises:
            ConnectionError: If FEP connection fails.
        """
        self._inner = io

        # Send connect PDU
        pdu = build_fep_connect_pdu(self.mst_addr, "000000")
        self._inner.write(pdu)

        # Read response
        response = self._inner.read()
        response_hex = response.hex().upper()

        if not (response_hex.startswith("68") and response_hex.endswith("16")):
            raise ConnectionError("Invalid FEP connect response format")

        if "68210000" not in response_hex:
            raise ConnectionError("FEP connection rejected")

        LOG.info("FEP connected", mst_addr=self.mst_addr)

    def get_devices(self) -> list:
        """Get list of registered devices from FEP.

        Returns:
            List of meter number strings.

        Raises:
            ConnectionError: If FEP communication fails.
        """
        pdu = build_fep_get_devices_pdu(self.mst_addr)
        self._inner.write(pdu)

        response = self._inner.read()
        response_hex = response.hex().upper()

        if not (response_hex.startswith("68") and response_hex.endswith("16")):
            raise ConnectionError("Invalid FEP get-devices response")

        devices = parse_get_devices_response(response)
        LOG.info("FEP devices retrieved", count=len(devices))
        return devices

    def disconnect(self) -> None:
        """Disconnect from FEP server.

        Sends disconnect PDU and closes underlying IO.
        """
        if self._inner is None:
            return

        try:
            pdu = build_fep_disconnect_pdu(self.mst_addr)
            self._inner.write(pdu)
            response = self._inner.read()
            response_hex = response.hex().upper()

            if "68220000" not in response_hex:
                LOG.warning("FEP disconnect may have failed")
        except Exception:
            LOG.warning("Error during FEP disconnect", exc_info=True)
        finally:
            self._inner = None

    def encode_apdu(self, apdu: bytes) -> bytes:
        """Encode DLMS APDU into FEP frame.

        Args:
            apdu: Raw DLMS APDU bytes.

        Returns:
            Complete FEP frame bytes.
        """
        return encode_fep_frame(
            mst_addr=self.mst_addr,
            meter_no=self.meter_no,
            apdu=apdu,
            src_wport=self.src_wport,
            dst_wport=self.dst_wport,
            use_gateway=self.use_gateway,
        )

    def write(self, data: bytes) -> None:
        """Write data (FEP frame) to transport.

        Args:
            data: FEP frame bytes to send.
        """
        if self._inner is None:
            raise ConnectionError("FEP transport not connected")
        self._inner.write(data)

    def read(self) -> bytes:
        """Read data from transport and extract APDU.

        Returns:
            Extracted DLMS APDU bytes.
        """
        if self._inner is None:
            raise ConnectionError("FEP transport not connected")
        raw = self._inner.read()
        return parse_fep_response(raw, strip_gateway=self.use_gateway)
