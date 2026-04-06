"""AXDR encode/decode benchmark using DLMS APDU data."""

import timeit
from dlms_cosem.a_xdr import AXdrDecoder

# Typical DLMS GetRequest-Response APDU data (read register value)
GET_RESPONSE_DATA = bytes([
    0xC1, 0x01, 0xC0, 0x01, 0x00, 0x06, 0x00, 0x00,
    0x01, 0x00, 0x00, 0xFF, 0x02, 0x12, 0x34, 0x56,
    0x78, 0x9A, 0xBC,
])

# GetRequest for active power (OBIS 1.0.21.7.0.255)
GET_REQUEST_DATA = bytes([
    0xC0, 0x01, 0xC0, 0x01, 0x00, 0x06, 0x00, 0x00,
    0x01, 0x00, 0x15, 0x07, 0x00, 0xFF,
])


def bench_axdr_decode_get_response():
    """Benchmark decoding a typical DLMS GetResponse."""
    for _ in range(1000):
        dec = AXdrDecoder(GET_RESPONSE_DATA)
        dec.get_bytes(1)  # tag
        dec.get_bytes(2)  # invoke id
        dec.get_bytes(1)  # tag
        dec.get_bytes(2)  # invoke id
        dec.get_bytes(1)  # result
        dec.get_bytes(1)  # data tag
        dec.get_bytes(1)  # structure length
        for _ in range(6):
            dec.get_bytes(1)  # OBIS bytes


def bench_axdr_decode_get_request():
    """Benchmark decoding a typical DLMS GetRequest."""
    for _ in range(1000):
        dec = AXdrDecoder(GET_REQUEST_DATA)
        dec.get_bytes(1)  # tag
        dec.get_bytes(2)  # invoke id
        dec.get_bytes(1)  # tag
        dec.get_bytes(2)  # invoke id
        dec.get_bytes(1)  # CI
        dec.get_bytes(6)  # OBIS
        dec.get_bytes(1)  # attribute index
        dec.get_bytes(1)  # selector


if __name__ == "__main__":
    print("AXDR Decode GetResponse:", timeit.timeit(bench_axdr_decode_get_response, number=100))
    print("AXDR Decode GetRequest:", timeit.timeit(bench_axdr_decode_get_request, number=100))
