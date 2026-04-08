"""Tests for DLMS Automation."""
import os
import json
import tempfile
import pytest
from dlms_cosem.automation import (
    MeterReading, CollectionTask, AnomalyRule, AnomalyEvent,
    DataStorage, InMemoryStorage, CsvStorage, JsonStorage, SqliteStorage,
    AnomalyDetector, CollectionScheduler,
)


class TestMeterReading:
    def test_auto_timestamp(self):
        r = MeterReading(meter_id="M001", obis_code="1.0.1.8.0.255", value=100)
        assert r.timestamp
        assert r.status == "ok"


class TestInMemoryStorage:
    def test_store_and_query(self):
        s = InMemoryStorage()
        r = MeterReading("M001", "1.0.1.8.0.255", 100, timestamp="2026-01-01T00:00:00")
        s.store(r)
        results = s.query("M001")
        assert len(results) == 1

    def test_query_by_obis(self):
        s = InMemoryStorage()
        s.store(MeterReading("M001", "1.0.1.8.0.255", 100, timestamp="t1"))
        s.store(MeterReading("M001", "1.0.32.7.0.255", 220, timestamp="t2"))
        results = s.query("M001", obis="1.0.1.8")
        assert len(results) == 1

    def test_query_by_time(self):
        s = InMemoryStorage()
        s.store(MeterReading("M001", "1.0.1.8.0.255", 100, timestamp="2026-01-01"))
        s.store(MeterReading("M001", "1.0.1.8.0.255", 200, timestamp="2026-01-02"))
        results = s.query("M001", start="2026-01-02")
        assert len(results) == 1


class TestCsvStorage:
    def test_csv_roundtrip(self):
        with tempfile.NamedTemporaryFile(suffix=".csv", delete=False) as f:
            path = f.name
        try:
            s = CsvStorage(path)
            r = MeterReading("M001", "1.0.1.8.0.255", 100, "kWh", "2026-01-01")
            s.store(r)
            results = s.query("M001")
            assert len(results) == 1
            assert results[0].value == "100"
        finally:
            os.unlink(path)


class TestJsonStorage:
    def test_json_roundtrip(self):
        with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as f:
            path = f.name
        try:
            s = JsonStorage(path)
            s.store(MeterReading("M001", "1.0.1.8.0.255", 100, timestamp="t1"))
            s.store(MeterReading("M001", "1.0.1.8.0.255", 200, timestamp="t2"))
            results = s.query("M001")
            assert len(results) == 2
        finally:
            os.unlink(path)


class TestSqliteStorage:
    def test_sqlite_roundtrip(self):
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
            path = f.name
        try:
            s = SqliteStorage(path)
            s.store(MeterReading("M001", "1.0.1.8.0.255", 100, timestamp="t1"))
            s.store(MeterReading("M001", "1.0.2.8.0.255", 50, timestamp="t2"))
            results = s.query("M001")
            assert len(results) == 2
            results2 = s.query("M001", obis="1.0.1.8")
            assert len(results2) == 1
            s.close()
        finally:
            os.unlink(path)

    def test_batch_store(self):
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
            path = f.name
        try:
            s = SqliteStorage(path)
            readings = [
                MeterReading("M001", "1.0.1.8.0.255", i, timestamp=f"t{i}")
                for i in range(10)
            ]
            s.store_batch(readings)
            assert len(s.query("M001")) == 10
            s.close()
        finally:
            os.unlink(path)


class TestAnomalyDetector:
    def test_sudden_increase(self):
        detector = AnomalyDetector()
        r1 = MeterReading("M001", "1.0.1.8.0.255", 100, timestamp="t1")
        detector.check(r1)
        r2 = MeterReading("M001", "1.0.1.8.0.255", 200, timestamp="t2")  # 100% increase
        events = detector.check(r2)
        assert len(events) >= 1
        assert events[0].rule_name == "sudden_change"

    def test_out_of_range(self):
        detector = AnomalyDetector()
        r = MeterReading("M001", "1.0.32.7.0.255", 100, timestamp="t1")  # < 180V
        events = detector.check(r)
        assert any(e.rule_name == "zero_voltage" for e in events)

    def test_normal_reading(self):
        detector = AnomalyDetector()
        r = MeterReading("M001", "1.0.1.8.0.255", 100, timestamp="t1")
        events = detector.check(r)
        assert len(events) == 0  # First reading, no history

    def test_custom_rule(self):
        detector = AnomalyDetector([])
        detector.add_rule(AnomalyRule("test", "1.0.1.8", "out_of_range", {"max_val": 50}))
        r = MeterReading("M001", "1.0.1.8.0.255", 100, timestamp="t1")
        events = detector.check(r)
        assert len(events) == 1


class TestCollectionScheduler:
    def test_collect_all_success(self):
        def read_func(meter_id, obis_list):
            return [
                MeterReading(meter_id, obis, 100, timestamp="t1")
                for obis in obis_list
            ]
        storage = InMemoryStorage()
        scheduler = CollectionScheduler(read_func, storage)
        scheduler.add_meter("M001", ["1.0.1.8.0.255", "1.0.32.7.0.255"])
        results = scheduler.collect_all()
        assert len(results) == 2
        assert len(storage.query("M001")) == 2

    def test_collect_all_failure(self):
        def read_func(meter_id, obis_list):
            raise ConnectionError("Timeout")
        storage = InMemoryStorage()
        scheduler = CollectionScheduler(read_func, storage)
        scheduler.add_meter("M001", ["1.0.1.8.0.255"])
        results = scheduler.collect_all()
        assert len(results) == 1
        assert results[0].status == "timeout"

    def test_generate_report(self):
        storage = InMemoryStorage()
        scheduler = CollectionScheduler(lambda m, o: [], storage)
        scheduler.add_meter("M001", ["1.0.1.8.0.255"])
        report = scheduler.generate_report()
        assert "DLMS Collection Report" in report
        assert "Tasks: 1" in report
