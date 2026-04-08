"""Gateway Frame implementation for GPRS/3G/4G routing.

The Gateway Frame format:
- Header: 0xE6 (gateway marker)
- Network ID: 1 byte (network identifier)
- Address Length: 2 bytes (physical device address length)
- Physical Device Address: N bytes (ASCII or hex encoded meter address)
- User Info: DLMS PDU data

Reference: DLMS Blue Book 8.4.4 Gateway Frame
"""

from typing import Union
import attr


@attr.s(auto_attribs=True)
class GatewayFrame:
    """
    Gateway Frame for GPRS/3G/4G routing.

    The gateway frame wraps DLMS/COSEM data with routing information
    for transmission over cellular networks.

    Attributes:
        network_id: Network identifier (default: 0x00)
        physical_address: Physical device address (meter number)
        user_info: DLMS PDU data to be wrapped
        src_wport: Source WPort (default: 16)
        dst_wport: Destination WPort (default: 1)
    """

    network_id: int = attr.ib(default=0x00)
    physical_address: str = attr.ib(default="")
    user_info: bytes = attr.ib(default=b"")
    src_wport: int = attr.ib(default=16)
    dst_wport: int = attr.ib(default=1)

    GATEWAY_HEADER: int = 0xE6

    @classmethod
    def from_bytes(cls, data: bytes) -> "GatewayFrame":
        """
        Parse Gateway Frame from bytes.

        Format: 0xE6 + NetworkID(1) + AddrLen(2) + Addr(N) + UserInfo
        """
        if len(data) < 4:
            raise ValueError(
                f"Gateway Frame must be at least 4 bytes, got {len(data)}"
            )

        idx = 0

        # Parse header
        header = data[idx]
        idx += 1

        if header != cls.GATEWAY_HEADER:
            raise ValueError(
                f"Invalid Gateway Frame header: 0x{header:02X}, "
                f"expected 0x{cls.GATEWAY_HEADER:02X}"
            )

        # Parse network ID
        network_id = data[idx]
        idx += 1

        # Parse address length
        addr_len = int.from_bytes(data[idx:idx+2], byteorder='big')
        idx += 2

        # Parse physical address
        physical_address = data[idx:idx+addr_len].decode('ascii', errors='ignore')
        idx += addr_len

        # User info is the rest
        user_info = data[idx:]

        # Extract WPorts from user info (Wrapper PDU header)
        if len(user_info) >= 8:
            src_wport = int.from_bytes(user_info[2:6], byteorder='big')
            dst_wport = int.from_bytes(user_info[6:10], byteorder='big')
        else:
            src_wport = 16
            dst_wport = 1

        return cls(
            network_id=network_id,
            physical_address=physical_address,
            user_info=user_info,
            src_wport=src_wport,
            dst_wport=dst_wport,
        )

    def to_bytes(self) -> bytes:
        """
        Build Gateway Frame bytes.

        Format: 0xE6 + NetworkID(1) + AddrLen(2) + Addr(N) + UserInfo
        """
        # Build user info (Wrapper PDU)
        user_info = self._build_wrapper_pdu()

        # Build gateway PDU
        addr_bytes = self.physical_address.encode('ascii')
        addr_len = len(addr_bytes)

        pdu = bytes([
            self.GATEWAY_HEADER,
            self.network_id
        ])
        pdu += addr_len.to_bytes(2, byteorder='big')
        pdu += addr_bytes
        pdu += user_info

        return pdu

    def _build_wrapper_pdu(self) -> bytes:
        """
        Build Wrapper PDU with WPorts and length.

        Format: 0x0001 + SrcWPort(4) + DstWPort(4) + Len(4) + Data
        """
        # 0x0001 is the source WPort for gateway
        header = b'\x00\x01'
        src_wport = self.src_wport.to_bytes(4, byteorder='big')
        dst_wport = self.dst_wport.to_bytes(4, byteorder='big')
        length = len(self.user_info).to_bytes(4, byteorder='big')

        return header + src_wport + dst_wport + length + self.user_info

    @property
    def wrapper_pdu(self) -> bytes:
        """Get the inner Wrapper PDU (without gateway header)."""
        return self._build_wrapper_pdu()


@attr.s(auto_attribs=True)
class GatewayResponseFrame:
    """
    Gateway Response Frame for parsing responses from gateway.

    The response uses 0xE7 marker instead of 0xE6.

    Attributes:
        network_id: Network identifier
        physical_address: Physical device address
        user_info: DLMS PDU response data
        src_wport: Source WPort from response
        dst_wport: Destination WPort from response
    """

    network_id: int = attr.ib(default=0x00)
    physical_address: str = attr.ib(default="")
    user_info: bytes = attr.ib(default=b"")
    src_wport: int = attr.ib(default=1)
    dst_wport: int = attr.ib(default=16)

    GATEWAY_RESPONSE_HEADER: int = 0xE7

    @classmethod
    def from_bytes(cls, data: bytes) -> "GatewayResponseFrame":
        """
        Parse Gateway Response Frame from bytes.

        Format: 0xE7 + NetworkID(1) + AddrLen(2) + Addr(N) + UserInfo
        """
        if len(data) < 4:
            raise ValueError(
                f"Gateway Response Frame must be at least 4 bytes, got {len(data)}"
            )

        idx = 0

        # Parse header
        header = data[idx]
        idx += 1

        if header != cls.GATEWAY_RESPONSE_HEADER:
            raise ValueError(
                f"Invalid Gateway Response header: 0x{header:02X}, "
                f"expected 0x{cls.GATEWAY_RESPONSE_HEADER:02X}"
            )

        # Parse network ID
        network_id = data[idx]
        idx += 1

        # Parse address length
        addr_len = int.from_bytes(data[idx:idx+2], byteorder='big')
        idx += 2

        # Parse physical address
        physical_address = data[idx:idx+addr_len].decode('ascii', errors='ignore')
        idx += addr_len

        # User info is the rest
        user_info = data[idx:]

        # Extract WPorts from user info (Wrapper PDU header)
        if len(user_info) >= 8:
            src_wport = int.from_bytes(user_info[2:6], byteorder='big')
            dst_wport = int.from_bytes(user_info[6:10], byteorder='big')
        else:
            src_wport = 1
            dst_wport = 16

        return cls(
            network_id=network_id,
            physical_address=physical_address,
            user_info=user_info,
            src_wport=src_wport,
            dst_wport=dst_wport,
        )

    def to_bytes(self) -> bytes:
        """
        Build Gateway Response Frame bytes.

        Format: 0xE7 + NetworkID(1) + AddrLen(2) + Addr(N) + UserInfo
        """
        # Build user info (Wrapper PDU)
        user_info = self._build_wrapper_pdu()

        # Build gateway PDU
        addr_bytes = self.physical_address.encode('ascii')
        addr_len = len(addr_bytes)

        pdu = bytes([
            self.GATEWAY_RESPONSE_HEADER,
            self.network_id
        ])
        pdu += addr_len.to_bytes(2, byteorder='big')
        pdu += addr_bytes
        pdu += user_info

        return pdu

    def _build_wrapper_pdu(self) -> bytes:
        """Build Wrapper PDU for response."""
        header = b'\x00\x01'
        src_wport = self.src_wport.to_bytes(4, byteorder='big')
        dst_wport = self.dst_wport.to_bytes(4, byteorder='big')
        length = len(self.user_info).to_bytes(4, byteorder='big')

        return header + src_wport + dst_wport + length + self.user_info

    @property
    def wrapper_pdu(self) -> bytes:
        """Get the inner Wrapper PDU (without gateway header)."""
        return self._build_wrapper_pdu()
