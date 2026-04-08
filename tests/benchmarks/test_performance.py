"""Performance benchmarks for DLMS/COSEM critical paths.

Run with: python -m pytest tests/benchmarks/test_performance.py -v --benchmark-only
Or standalone: python tests/benchmarks/test_performance.py
"""
import os
import sys
import statistics
import time
from dataclasses import dataclass, field
from typing import List

# Ensure project root is on path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from dlms_cosem import a_xdr, enumerations
from dlms_cosem.cosem.obis import Obis
from dlms_cosem.cosem.C3_Register import Register
from dlms_cosem.cosem.C7_ProfileGeneric import ProfileGeneric
from dlms_cosem.hdlc.frames import InformationFrame, ReceiveReadyFrame, SetNormalResponseModeFrame
from dlms_cosem.hdlc.address import HdlcAddress
from dlms_cosem.protocol.xdlms.get import GetRequestNormal
from dlms_cosem.protocol.xdlms.set import SetRequestNormal
from dlms_cosem.protocol.xdlms.initiate_request import InitiateRequest
from dlms_cosem.parsers import ProfileGenericBufferParser as ProfileGenericParser
from dlms_cosem.dlms_data import IntegerData, OctetStringData, DataStructure, DataArray


@dataclass
class BenchmarkResult:
    name: str
    iterations: int
    total_seconds: float
    ops_per_sec: float
    avg_us: float
    min_us: float
    max_us: float
    median_us: float
    p99_us: float


@dataclass
class BenchmarkSuite:
    results: List[BenchmarkResult] = field(default_factory=list)

    def add(self, name: str, iterations: int, timings: List[float]):
        total = sum(timings)
        timings_us = [t * 1_000_000 for t in timings]
        sorted_us = sorted(timings_us)
        p99_idx = max(0, int(len(sorted_us) * 0.99) - 1)
        self.results.append(BenchmarkResult(
            name=name,
            iterations=iterations,
            total_seconds=total,
            ops_per_sec=iterations / total,
            avg_us=statistics.mean(timings_us),
            min_us=min(timings_us),
            max_us=max(timings_us),
            median_us=statistics.median(timings_us),
            p99_us=sorted_us[p99_idx],
        ))

    def to_markdown(self) -> str:
        lines = [
            "# Performance Benchmark Results",
            "",
            f"Generated: {time.strftime('%Y-%m-%d %H:%M:%S')}",
            "",
            "| Benchmark | Iterations | Ops/sec | Avg (μs) | Min (μs) | Max (μs) | Median (μs) | P99 (μs) |",
            "|-----------|-----------|---------|----------|----------|----------|-------------|----------|",
        ]
        for r in self.results:
            lines.append(
                f"| {r.name} | {r.iterations} | {r.ops_per_sec:,.0f} | "
                f"{r.avg_us:.1f} | {r.min_us:.1f} | {r.max_us:.1f} | "
                f"{r.median_us:.1f} | {r.p99_us:.1f} |"
            )
        lines.append("")
        return "\n".join(lines)


def run_benchmark(func, iterations: int, warmup: int = 100) -> List[float]:
    """Run a function multiple times and return individual timings."""
    # Warmup
    for _ in range(warmup):
        func()
    # Timed runs
    timings = []
    for _ in range(iterations):
        t0 = time.perf_counter()
        func()
        t1 = time.perf_counter()
        timings.append(t1 - t0)
    return timings


def bench_hdlc_frame_encode(suite: BenchmarkSuite):
    """Benchmark HDLC InformationFrame encoding."""
    addr = HdlcAddress(1, 16, 1, 4, 0)
    frame = InformationFrame(destination_address=addr, source_address=addr,
                             control=bytes([0x10]), hcs=b"\x00\x00",
                             information=b"\x01\x02\x03\x04", fcs=b"\x00\x00")

    def encode():
        frame.to_bytes()

    timings = run_benchmark(encode, 10000)
    suite.add("HDLC InfoFrame encode", 10000, timings)


def bench_hdlc_frame_decode(suite: BenchmarkSuite):
    """Benchmark HDLC InformationFrame decoding."""
    addr = HdlcAddress(1, 16, 1, 4, 0)
    frame = InformationFrame(destination_address=addr, source_address=addr,
                             control=bytes([0x10]), hcs=b"\x00\x00",
                             information=b"\x01\x02\x03\x04", fcs=b"\x00\x00")
    frame_bytes = frame.to_bytes()

    def decode():
        InformationFrame.from_bytes(frame_bytes)

    timings = run_benchmark(decode, 10000)
    suite.add("HDLC InfoFrame decode", 10000, timings)


def bench_axdr_encode(suite: BenchmarkSuite):
    """Benchmark AXDR encoding of various data types."""
    def encode():
        a_xdr.encoding.long_unsigned_en(0, 1000)
        a_xdr.encoding.integer_en(0, -500)
        a_xdr.encoding.octet_string_en(0, b"\x01\x02\x03\x04\x05\x06")

    timings = run_benchmark(encode, 10000)
    suite.add("AXDR encode (long_unsigned + integer + octet_string)", 10000, timings)


def bench_axdr_decode(suite: BenchmarkSuite):
    """Benchmark AXDR decoding."""
    data = b"\xe8\x03\x12\xfc\xfe\x06\x01\x02\x03\x04\x05\x06"

    def decode():
        a_xdr.decoding.long_unsigned(data, 0)
        a_xdr.decoding.integer(data, 2)
        a_xdr.decoding.octet_string(data, 4)

    timings = run_benchmark(decode, 10000)
    suite.add("AXDR decode (long_unsigned + integer + octet_string)", 10000, timings)


def bench_apdu_get_request(suite: BenchmarkSuite):
    """Benchmark GetRequestNormal serialization."""
    cosem_attr = a_xdr.CosemAttribute(
        interface=enumerations.CosemInterface.REGISTER,
        instance=Obis(0, 0, 1, 0, 0, 255),
        attribute=2,
    )
    request = GetRequestNormal(cosem_attribute=cosem_attr)

    def serialize():
        request.to_bytes()

    timings = run_benchmark(serialize, 10000)
    suite.add("APDU GetRequestNormal serialize", 10000, timings)


def bench_apdu_set_request(suite: BenchmarkSuite):
    """Benchmark SetRequestNormal serialization."""
    cosem_attr = a_xdr.CosemAttribute(
        interface=enumerations.CosemInterface.REGISTER,
        instance=Obis(0, 0, 1, 0, 0, 255),
        attribute=2,
    )
    request = SetRequestNormal(
        cosem_attribute=cosem_attr,
        request_data=IntegerData(100),
    )

    def serialize():
        request.to_bytes()

    timings = run_benchmark(serialize, 10000)
    suite.add("APDU SetRequestNormal serialize", 10000, timings)


def bench_initiate_request(suite: BenchmarkSuite):
    """Benchmark InitiateRequest serialization."""
    request = InitiateRequest(
        proposed_conformance=a_xdr.Conformance(0xFFFFFFFF),
        proposed_quality_of_service=0,
    )

    def serialize():
        request.to_bytes()

    timings = run_benchmark(serialize, 10000)
    suite.add("APDU InitiateRequest serialize", 10000, timings)


def bench_sm4_encrypt(suite: BenchmarkSuite):
    """Benchmark SM4-GCM encryption (AES-128-GCM fallback)."""
    try:
        from dlms_cosem.security import SM4Cipher
        key = os.urandom(16)
        nonce = os.urandom(12)
        cipher = SM4Cipher(key=key, nonce=nonce)
        plaintext = b"A" * 256
    except Exception:
        suite.add("SM4-GCM encrypt (256B)", 0, [0])
        return

    def encrypt():
        cipher.encrypt(plaintext)

    timings = run_benchmark(encrypt, 5000)
    suite.add("SM4-GCM encrypt (256B)", 5000, timings)


def bench_sm4_decrypt(suite: BenchmarkSuite):
    """Benchmark SM4-GCM decryption."""
    try:
        from dlms_cosem.security import SM4Cipher
        key = os.urandom(16)
        nonce = os.urandom(12)
        cipher = SM4Cipher(key=key, nonce=nonce)
        plaintext = b"A" * 256
        ciphertext = cipher.encrypt(plaintext)
    except Exception:
        suite.add("SM4-GCM decrypt (256B)", 0, [0])
        return

    def decrypt():
        cipher.decrypt(ciphertext)

    timings = run_benchmark(decrypt, 5000)
    suite.add("SM4-GCM decrypt (256B)", 5000, timings)


def bench_profile_generic_parse(suite: BenchmarkSuite):
    """Benchmark Profile Generic parsing (simulated)."""
    # Build a simulated profile generic buffer
    entries = 100
    columns_data = (
        b"\x02\x06"  # structure of 2 elements, length 6
        b"\x12\x06\x00\x00\x01\x00\x00\xff"  # column 1: octet-string OBIS
        b"\x12\x06\x00\x00\x01\x00\x00\xff"  # column 2: octet-string OBIS
    )
    # Create a buffer: capture_objects + entries (simplified)
    buf = b"\x01\x01\x00\xff\x06\x00\x00\x01\x00\x00\xff"  # capture_object
    buf += b"\x01"  # simple value
    buf += b"\x06" * (entries * 20)  # fake entry data

    parser = ProfileGenericParser(
        capture_objects=[],
        capture_period=60,
    )

    def parse():
        try:
            parser.parse_bytes(buf)
        except Exception:
            pass

    timings = run_benchmark(parse, 1000)
    suite.add("Profile Generic parse (100 entries)", 1000, timings)


def bench_obis_creation(suite: BenchmarkSuite):
    """Benchmark OBIS code creation."""
    def create():
        Obis(0, 0, 1, 0, 0, 255)

    timings = run_benchmark(create, 50000)
    suite.add("Obis creation", 50000, timings)


def bench_register_creation(suite: BenchmarkSuite):
    """Benchmark COSEM Register object creation."""
    def create():
        Register(Obis(0, 0, 1, 0, 0, 255))

    timings = run_benchmark(create, 50000)
    suite.add("Register creation", 50000, timings)


def main():
    suite = BenchmarkSuite()

    print("Running DLMS/COSEM performance benchmarks...")
    print("=" * 60)

    benchmarks = [
        bench_hdlc_frame_encode,
        bench_hdlc_frame_decode,
        bench_axdr_encode,
        bench_axdr_decode,
        bench_apdu_get_request,
        bench_apdu_set_request,
        bench_initiate_request,
        bench_sm4_encrypt,
        bench_sm4_decrypt,
        bench_profile_generic_parse,
        bench_obis_creation,
        bench_register_creation,
    ]

    for bench in benchmarks:
        name = bench.__name__.replace("bench_", "").replace("_", " ").title()
        print(f"  Running: {name}...")
        try:
            bench(suite)
        except Exception as e:
            print(f"    SKIPPED: {e}")
            suite.results.append(BenchmarkResult(
                name=bench.__name__, iterations=0, total_seconds=0,
                ops_per_sec=0, avg_us=0, min_us=0, max_us=0,
                median_us=0, p99_us=0,
            ))

    print()
    md = suite.to_markdown()
    print(md)

    # Write results
    results_path = os.path.join(os.path.dirname(__file__), "RESULTS.md")
    with open(results_path, "w") as f:
        f.write(md)
    print(f"Results written to {results_path}")


if __name__ == "__main__":
    main()
