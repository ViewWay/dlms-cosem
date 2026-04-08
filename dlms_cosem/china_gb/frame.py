"""China GB DLMS/T CP 28 frame handling."""
from __future__ import annotations

from dataclasses import dataclass

from dlms_cosem.china_gb.types import GBCp28Command


@dataclass
class GBRS485Config:
    """China standard RS485 communication parameters."""
    baud_rate: int = 2400
    data_bits: int = 8
    stop_bits: int = 1
    parity: str = "even"  # even, odd, none
    address_length: int = 12  # meter address length (bytes)
    password: bytes | None = None
    timeout_ms: int = 5000

    @property
    def parity_char(self) -> str:
        return {"even": "E", "odd": "O", "none": "N"}[self.parity]

    @property
    def serial_config(self) -> str:
        return f"{self.baud_rate},{self.data_bits},{self.parity_char},{self.stop_bits}"

    @classmethod
    def from_string(cls, config: str) -> "GBRS485Config":
        """Parse serial config string like '2400,8,E,1'."""
        parts = config.split(",")
        return cls(
            baud_rate=int(parts[0]),
            data_bits=int(parts[1]),
            parity={"E": "even", "O": "odd", "N": "none"}[parts[2]],
            stop_bits=int(parts[3]),
        )


@dataclass
class GBCp28Frame:
    """DLMS/T CP 28 frame (China local protocol frame)."""
    address: bytes
    control: int = 0x13
    command: GBCp28Command = GBCp28Command.READ_DATA
    data_length: int = 0
    data: bytes = b""
    checksum: int = 0

    def to_bytes(self) -> bytes:
        """Encode CP 28 frame."""
        frame = bytearray()
        frame.append(0x68)  # Start
        frame.extend(self.address)
        frame.append(self.control)
        frame.append(self.command)
        frame.append(len(self.data))
        frame.extend(self.data)
        # Checksum: XOR of all bytes after start marker
        checksum = 0
        for b in frame[1:]:
            checksum ^= b
        frame.append(checksum)
        frame.append(0x16)  # End
        return bytes(frame)

    @classmethod
    def from_bytes(cls, data: bytes) -> "GBCp28Frame":
        """Decode CP 28 frame."""
        if len(data) < 10 or data[0] != 0x68:
            raise ValueError("Invalid CP 28 frame")

        addr_len = 6  # Standard address length
        address = data[1:1 + addr_len]
        control = data[1 + addr_len]
        command = GBCp28Command(data[2 + addr_len])
        data_len = data[3 + addr_len]
        payload = data[4 + addr_len:4 + addr_len + data_len]
        checksum = data[4 + addr_len + data_len]

        return cls(
            address=address,
            control=control,
            command=command,
            data_length=data_len,
            data=payload,
            checksum=checksum,
        )
