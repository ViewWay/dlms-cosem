"""HDLC benchmark: frame header parsing and CRC operations."""

import timeit
from dlms_cosem.hdlc.frames import BaseHdlcFrame
from dlms_cosem.crc import CRCCCITT

# Typical DLMS APDU payload
APDU_PAYLOAD = bytes([
    0xC0, 0x01, 0xC0, 0x01, 0x00, 0x06, 0x00, 0x00,
    0x01, 0x00, 0x15, 0x07, 0x00, 0xFF,
])

# Pre-compute CRC for benchmark
crc = CRCCCITT()
_fcs = crc.calculate_for(APDU_PAYLOAD)


def bench_crc_calculate():
    """Benchmark CRC-16 CCITT on DLMS APDU."""
    for _ in range(1000):
        crc.calculate_for(APDU_PAYLOAD)


def bench_frame_length():
    """Benchmark HDLC frame format field parsing."""
    frame_bytes = bytes([0x7E, 0xA6, 0x08, 0x13] + list(APDU_PAYLOAD) + [0x00, 0x00, 0x7E])
    for _ in range(1000):
        frame_is_enclosed_by_hdlc_flags(frame_bytes)


def frame_is_enclosed_by_hdlc_flags(frame_bytes: bytes):
    return frame_bytes[0] == 0x7E and frame_bytes[-1] == 0x7E


if __name__ == "__main__":
    print("CRC-16 CCITT (14B):", timeit.timeit(bench_crc_calculate, number=100))
    print("Frame flag check:", timeit.timeit(bench_frame_length, number=100))
