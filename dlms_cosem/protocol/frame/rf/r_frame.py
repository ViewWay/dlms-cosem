"""RF (Radio Frequency) Frame implementation for wireless DLMS.

The RF Frame format supports wireless meter reading with channel scanning,
signal quality reporting, and CRC16 integrity checks.

Format:
- Start Bit: 0x68
- DCU Address: 8 bytes (data concentrator unit)
- Communication Type: 2 bytes (0x21=Read, 0x22=Command, etc.)
- Meter Address: 16 bytes (meter serial number)
- Control Character 1: 2 bytes (command control)
- Control Character 2: 2 bytes (reserved, usually 0x00)
- Frame Sequence Number: 2 bytes
- Data Length: 2 bytes
- Data APDU: N bytes (actual DLMS data)
- Uplink Signal Strength: 2 bytes
- Uplink SNR: 2 bytes (signal-to-noise ratio)
- Downlink Signal Strength: 2 bytes
- Downlink SNR: 2 bytes
- Link State Word: 2 bytes
- Channel State Word: 2 bytes
- CRC16: 4 bytes (CRC-16/CCITT)
- End Bit: 0x16

Reference: Chinese GB/T 17215.211-2019 and DLMS Wireless
"""

from typing import Optional, Union
import attr
import struct


def crc16_ccitt(data: bytes) -> bytes:
    """
    Calculate CRC-16/CCITT (Kermit) checksum.

    Polynomial: 0x1021
    Initial: 0x0000
    XorOut: 0x0000
    """
    crc = 0x0000
    for byte in data:
        crc ^= byte
        for _ in range(8):
            if crc & 0x0001:
                crc = (crc >> 1) ^ 0x1021
            else:
                crc >>= 1
    return struct.pack('<H', crc)


@attr.s(auto_attribs=True)
class RFSignalQuality:
    """
    RF signal quality metrics.

    Attributes:
        uplink_signal_strength: Uplink RSSI (0-255)
        uplink_snr: Uplink signal-to-noise ratio (0-255)
        downlink_signal_strength: Downlink RSSI (0-255)
        downlink_snr: Downlink signal-to-noise ratio (0-255)
    """

    uplink_signal_strength: int = attr.ib(default=0)
    uplink_snr: int = attr.ib(default=0)
    downlink_signal_strength: int = attr.ib(default=0)
    downlink_snr: int = attr.ib(default=0)

    @classmethod
    def from_bytes(cls, data: bytes) -> "RFSignalQuality":
        """Parse signal quality from 8 bytes (2 bytes per field)."""
        if len(data) < 8:
            raise ValueError(
                f"RFSignalQuality requires 8 bytes, got {len(data)}"
            )

        uplink_rssi = int.from_bytes(data[0:2], byteorder='big')
        uplink_snr = int.from_bytes(data[2:4], byteorder='big')
        downlink_rssi = int.from_bytes(data[4:6], byteorder='big')
        downlink_snr = int.from_bytes(data[6:8], byteorder='big')

        return cls(
            uplink_signal_strength=uplink_rssi,
            uplink_snr=uplink_snr,
            downlink_signal_strength=downlink_rssi,
            downlink_snr=downlink_snr,
        )

    def to_bytes(self) -> bytes:
        """Encode signal quality to 8 bytes (2 bytes per field)."""
        return (
            self.uplink_signal_strength.to_bytes(2, byteorder='big') +
            self.uplink_snr.to_bytes(2, byteorder='big') +
            self.downlink_signal_strength.to_bytes(2, byteorder='big') +
            self.downlink_snr.to_bytes(2, byteorder='big')
        )


@attr.s(auto_attribs=True)
class RFChannelState:
    """
    RF channel state information.

    Attributes:
        link_state: Link state word
        channel_state: Channel state word
    """

    link_state: int = attr.ib(default=0)
    channel_state: int = attr.ib(default=0)

    @classmethod
    def from_bytes(cls, data: bytes) -> "RFChannelState":
        """Parse channel state from 4 bytes (2 bytes per field)."""
        if len(data) < 4:
            raise ValueError(
                f"RFChannelState requires 4 bytes, got {len(data)}"
            )

        link_state = int.from_bytes(data[0:2], byteorder='big')
        channel_state = int.from_bytes(data[2:4], byteorder='big')

        return cls(
            link_state=link_state,
            channel_state=channel_state,
        )

    def to_bytes(self) -> bytes:
        """Encode channel state to 4 bytes (2 bytes per field)."""
        return (
            self.link_state.to_bytes(2, byteorder='big') +
            self.channel_state.to_bytes(2, byteorder='big')
        )


@attr.s(auto_attribs=True)
class RFFrame:
    """
    RF (Radio Frequency) Frame for wireless DLMS communication.

    This frame format is used for ISM band wireless communication
    (e.g., 470MHz in China) with meters.

    Attributes:
        dcu_address: Data Concentrator Unit address (8 bytes hex)
        meter_address: Meter serial number (16 bytes hex)
        communication_type: Communication type (0x21=Read, 0x22=Command, etc.)
        control_char1: Control character 1
        control_char2: Control character 2 (reserved, default 0x00)
        frame_sequence: Frame sequence number
        data_apdu: DLMS APDU data
        signal_quality: RF signal quality metrics
        channel_state: RF channel state information
    """

    dcu_address: bytes = attr.ib(default=b'\x00' * 8)
    meter_address: bytes = attr.ib(default=b'\x00' * 16)
    communication_type: int = attr.ib(default=0x21)
    control_char1: int = attr.ib(default=0x1E)
    control_char2: int = attr.ib(default=0x00)
    frame_sequence: int = attr.ib(default=0x01)
    data_apdu: bytes = attr.ib(default=b"")
    signal_quality: RFSignalQuality = attr.ib(factory=RFSignalQuality)
    channel_state: RFChannelState = attr.ib(factory=RFChannelState)

    START_BIT: int = 0x68
    END_BIT: int = 0x16

    # Communication types
    COMM_TYPE_READ: int = 0x21
    COMM_TYPE_COMMAND: int = 0x22

    @classmethod
    def from_bytes(cls, data: bytes) -> "RFFrame":
        """
        Parse RF Frame from bytes.

        Format: 0x68 + DCUAddr(8) + CommType(2) + MeterAddr(16) +
                Ctrl1(2) + Ctrl2(2) + Seq(2) + Len(2) + Data(N) +
                Signal(8) + State(4) + CRC(4) + 0x16
        """
        if len(data) < 40:
            raise ValueError(
                f"RF Frame must be at least 40 bytes, got {len(data)}"
            )

        idx = 0

        # Parse start bit
        start_bit = data[idx]
        idx += 1
        if start_bit != cls.START_BIT:
            raise ValueError(
                f"Invalid RF Frame start bit: 0x{start_bit:02X}, "
                f"expected 0x{cls.START_BIT:02X}"
            )

        # Parse DCU address
        dcu_address = data[idx:idx+8]
        idx += 8

        # Parse communication type
        comm_type = int.from_bytes(data[idx:idx+2], byteorder='big')
        idx += 2

        # Parse meter address
        meter_address = data[idx:idx+16]
        idx += 16

        # Parse control characters
        ctrl1 = int.from_bytes(data[idx:idx+2], byteorder='big')
        idx += 2
        ctrl2 = int.from_bytes(data[idx:idx+2], byteorder='big')
        idx += 2

        # Parse frame sequence
        frame_seq = int.from_bytes(data[idx:idx+2], byteorder='big')
        idx += 2

        # Parse data length
        data_len = int.from_bytes(data[idx:idx+2], byteorder='big')
        idx += 2

        # Parse data APDU
        data_apdu = data[idx:idx+data_len]
        idx += data_len

        # Parse signal quality
        signal_quality = RFSignalQuality.from_bytes(data[idx:idx+8])
        idx += 8

        # Parse channel state
        channel_state = RFChannelState.from_bytes(data[idx:idx+4])
        idx += 4

        # At this point, idx points to the CRC field
        # CRC covers from start_bit (index 0) to end of channel_state (index idx-1)
        crc_data = data[:idx]  # All data before CRC
        crc_received = int.from_bytes(data[idx:idx+4], byteorder='big')
        idx += 4

        crc_calculated = int.from_bytes(crc16_ccitt(crc_data), byteorder='big')
        if crc_received != crc_calculated:
            raise ValueError(
                f"RF Frame CRC mismatch: received 0x{crc_received:04X}, "
                f"calculated 0x{crc_calculated:04X}"
            )

        # Parse end bit
        if idx >= len(data):
            raise ValueError(
                f"RF Frame truncated: missing end bit at index {idx}"
            )
        end_bit = data[idx]
        if end_bit != cls.END_BIT:
            raise ValueError(
                f"Invalid RF Frame end bit: 0x{end_bit:02X}, "
                f"expected 0x{cls.END_BIT:02X}"
            )

        return cls(
            dcu_address=dcu_address,
            meter_address=meter_address,
            communication_type=comm_type,
            control_char1=ctrl1,
            control_char2=ctrl2,
            frame_sequence=frame_seq,
            data_apdu=data_apdu,
            signal_quality=signal_quality,
            channel_state=channel_state,
        )

    def to_bytes(self) -> bytes:
        """
        Build RF Frame bytes.

        Format: 0x68 + DCUAddr(8) + CommType(2) + MeterAddr(16) +
                Ctrl1(2) + Ctrl2(2) + Seq(2) + Len(2) + Data(N) +
                Signal(8) + State(4) + CRC(4) + 0x16
        """
        # Build frame components
        frame = bytearray()

        # Start bit
        frame.append(self.START_BIT)

        # DCU address
        frame.extend(self.dcu_address)

        # Communication type
        frame.extend(self.communication_type.to_bytes(2, byteorder='big'))

        # Meter address
        frame.extend(self.meter_address)

        # Control characters
        frame.extend(self.control_char1.to_bytes(2, byteorder='big'))
        frame.extend(self.control_char2.to_bytes(2, byteorder='big'))

        # Frame sequence
        frame.extend(self.frame_sequence.to_bytes(2, byteorder='big'))

        # Data length and data APDU
        data_len = len(self.data_apdu)
        frame.extend(data_len.to_bytes(2, byteorder='big'))
        frame.extend(self.data_apdu)

        # Signal quality
        frame.extend(self.signal_quality.to_bytes())

        # Channel state
        frame.extend(self.channel_state.to_bytes())

        # Calculate CRC
        crc = crc16_ccitt(bytes(frame))
        frame.extend(crc)

        # End bit
        frame.append(self.END_BIT)

        return bytes(frame)

    def scan_channel(self, channel: int) -> bytes:
        """
        Generate channel scan frame for specified channel.

        Args:
            channel: Channel number (1-5)

        Returns:
            RF Frame bytes for channel scan
        """
        if not 1 <= channel <= 5:
            raise ValueError(f"Channel must be 1-5, got {channel}")

        # Build scan data APDU
        scan_data = bytes.fromhex("0107F08BA73609")

        # Encode channel as 3 bits + fixed "00111" suffix (8 bits total)
        # channel_bits: 3 bits for channel number (1-5)
        channel_bits = (channel & 0x07)  # Ensure 3 bits
        channel_byte = (channel_bits << 5) | 0x07  # channel in high 3 bits, 0x07 in low 5 bits

        scan_data += bytes([channel_byte])

        scan_frame = self.__class__(
            communication_type=self.COMM_TYPE_COMMAND,
            control_char1=0x42,
            frame_sequence=channel,
            data_apdu=scan_data,
        )

        return scan_frame.to_bytes()

    def connect_meter(self, channel: int) -> bytes:
        """
        Generate connect meter frame for specified channel.

        Args:
            channel: Channel number (1-5)

        Returns:
            RF Frame bytes for meter connection
        """
        connect_data = b'\x5A'

        connect_frame = self.__class__(
            communication_type=self.COMM_TYPE_READ,
            control_char1=0x1C,
            frame_sequence=channel + 1,
            data_apdu=connect_data,
        )

        return connect_frame.to_bytes()

    def negotiate_parameters(self, channel: int) -> bytes:
        """
        Generate parameter negotiation frame for specified channel.

        Args:
            channel: Channel number (1-5)

        Returns:
            RF Frame bytes for parameter negotiation
        """
        negotiate_data = bytes.fromhex("02023C03")

        negotiate_frame = self.__class__(
            communication_type=self.COMM_TYPE_READ,
            control_char1=0x1D,
            frame_sequence=channel + 2,
            data_apdu=negotiate_data,
        )

        return negotiate_frame.to_bytes()
