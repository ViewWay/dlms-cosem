"""DLMS Data Collection Automation.

Provides batch meter reading, scheduled collection, data storage
(CSV/JSON/SQLite), anomaly detection, and collection reporting.
"""
import csv
import io
import json
import os
import sqlite3
import structlog
from dataclasses import dataclass, field, asdict
from datetime import datetime, timedelta
from typing import Any, Callable, Dict, List, Optional, Tuple

LOG = structlog.get_logger()


@dataclass
class MeterReading:
    """A single meter reading."""
    meter_id: str
    obis_code: str
    value: Any
    unit: str = ""
    timestamp: str = ""
    status: str = "ok"  # ok, missing, abnormal, timeout

    def __post_init__(self):
        if not self.timestamp:
            self.timestamp = datetime.now().isoformat()


@dataclass
class CollectionTask:
    """A data collection task definition."""
    meter_id: str
    obis_list: List[str]
    interval_seconds: int = 900  # 15 min default
    retry_count: int = 3
    timeout_seconds: int = 30
    enabled: bool = True


@dataclass
class AnomalyRule:
    """Rule for anomaly detection."""
    name: str
    obis_pattern: str  # OBIS prefix to match, e.g. "1.0.1.8"
    check_type: str  # sudden_change, missing, out_of_range, zero_flow
    params: Dict[str, Any] = field(default_factory=dict)


@dataclass
class AnomalyEvent:
    """Detected anomaly event."""
    meter_id: str
    obis_code: str
    rule_name: str
    value: Any
    expected: Any
    timestamp: str = ""
    severity: str = "warning"  # info, warning, critical

    def __post_init__(self):
        if not self.timestamp:
            self.timestamp = datetime.now().isoformat()


class DataStorage:
    """Storage backend for collected meter data."""

    def store(self, reading: MeterReading) -> None:
        raise NotImplementedError

    def store_batch(self, readings: List[MeterReading]) -> None:
        for r in readings:
            self.store(r)

    def query(
        self, meter_id: str, obis: Optional[str] = None,
        start: Optional[str] = None, end: Optional[str] = None,
    ) -> List[MeterReading]:
        raise NotImplementedError


class InMemoryStorage(DataStorage):
    """In-memory storage (for testing)."""

    def __init__(self):
        self._data: List[MeterReading] = []

    def store(self, reading: MeterReading) -> None:
        self._data.append(reading)

    def query(
        self, meter_id: str, obis: Optional[str] = None,
        start: Optional[str] = None, end: Optional[str] = None,
    ) -> List[MeterReading]:
        results = [r for r in self._data if r.meter_id == meter_id]
        if obis:
            results = [r for r in results if obis in r.obis_code]
        if start:
            results = [r for r in results if r.timestamp >= start]
        if end:
            results = [r for r in results if r.timestamp <= end]
        return results


class CsvStorage(DataStorage):
    """CSV file storage."""

    def __init__(self, filepath: str):
        self.filepath = filepath
        self._init_file()

    def _init_file(self) -> None:
        if not os.path.exists(self.filepath) or os.path.getsize(self.filepath) == 0:
            with open(self.filepath, "w", newline="") as f:
                writer = csv.writer(f)
                writer.writerow(["meter_id", "obis_code", "value", "unit", "timestamp", "status"])

    def store(self, reading: MeterReading) -> None:
        with open(self.filepath, "a", newline="") as f:
            writer = csv.writer(f)
            writer.writerow([
                reading.meter_id, reading.obis_code, reading.value,
                reading.unit, reading.timestamp, reading.status,
            ])

    def query(
        self, meter_id: str, obis: Optional[str] = None,
        start: Optional[str] = None, end: Optional[str] = None,
    ) -> List[MeterReading]:
        results = []
        with open(self.filepath, "r", newline="") as f:
            reader = csv.DictReader(f)
            for row in reader:
                if row["meter_id"] != meter_id:
                    continue
                if obis and obis not in row["obis_code"]:
                    continue
                if start and row["timestamp"] < start:
                    continue
                if end and row["timestamp"] > end:
                    continue
                results.append(MeterReading(
                    meter_id=row["meter_id"],
                    obis_code=row["obis_code"],
                    value=row["value"],
                    unit=row.get("unit", ""),
                    timestamp=row["timestamp"],
                    status=row.get("status", "ok"),
                ))
        return results


class JsonStorage(DataStorage):
    """JSON file storage."""

    def __init__(self, filepath: str):
        self.filepath = filepath
        self._data: List[dict] = []
        self._load()

    def _load(self) -> None:
        if os.path.exists(self.filepath) and os.path.getsize(self.filepath) > 0:
            with open(self.filepath, "r") as f:
                self._data = json.load(f)

    def _save(self) -> None:
        with open(self.filepath, "w") as f:
            json.dump(self._data, f, indent=2, default=str)

    def store(self, reading: MeterReading) -> None:
        self._data.append(asdict(reading))
        self._save()

    def query(
        self, meter_id: str, obis: Optional[str] = None,
        start: Optional[str] = None, end: Optional[str] = None,
    ) -> List[MeterReading]:
        results = []
        for d in self._data:
            if d["meter_id"] != meter_id:
                continue
            if obis and obis not in d["obis_code"]:
                continue
            if start and d["timestamp"] < start:
                continue
            if end and d["timestamp"] > end:
                continue
            results.append(MeterReading(**d))
        return results


class SqliteStorage(DataStorage):
    """SQLite storage backend."""

    def __init__(self, db_path: str = "dlms_data.db"):
        self.db_path = db_path
        self.conn = sqlite3.connect(db_path)
        self._init_db()

    def _init_db(self) -> None:
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS readings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                meter_id TEXT NOT NULL,
                obis_code TEXT NOT NULL,
                value TEXT,
                unit TEXT DEFAULT '',
                timestamp TEXT NOT NULL,
                status TEXT DEFAULT 'ok'
            )
        """)
        self.conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_meter_obis
            ON readings(meter_id, obis_code, timestamp)
        """)
        self.conn.commit()

    def store(self, reading: MeterReading) -> None:
        self.conn.execute(
            "INSERT INTO readings (meter_id, obis_code, value, unit, timestamp, status) VALUES (?,?,?,?,?,?)",
            (reading.meter_id, reading.obis_code, str(reading.value),
             reading.unit, reading.timestamp, reading.status),
        )
        self.conn.commit()

    def store_batch(self, readings: List[MeterReading]) -> None:
        self.conn.executemany(
            "INSERT INTO readings (meter_id, obis_code, value, unit, timestamp, status) VALUES (?,?,?,?,?,?)",
            [(r.meter_id, r.obis_code, str(r.value), r.unit, r.timestamp, r.status) for r in readings],
        )
        self.conn.commit()

    def query(
        self, meter_id: str, obis: Optional[str] = None,
        start: Optional[str] = None, end: Optional[str] = None,
    ) -> List[MeterReading]:
        query = "SELECT meter_id, obis_code, value, unit, timestamp, status FROM readings WHERE meter_id=?"
        params: list = [meter_id]
        if obis:
            query += " AND obis_code LIKE ?"
            params.append(f"%{obis}%")
        if start:
            query += " AND timestamp >= ?"
            params.append(start)
        if end:
            query += " AND timestamp <= ?"
            params.append(end)
        query += " ORDER BY timestamp"
        rows = self.conn.execute(query, params).fetchall()
        return [MeterReading(meter_id=r[0], obis_code=r[1], value=r[2],
                             unit=r[3], timestamp=r[4], status=r[5]) for r in rows]

    def close(self) -> None:
        self.conn.close()


class AnomalyDetector:
    """Detects anomalies in meter readings."""

    def __init__(self, rules: Optional[List[AnomalyRule]] = None):
        self.rules = rules or self._default_rules()
        self._history: Dict[str, List[Tuple[str, Any]]] = {}  # obis -> [(ts, value)]

    @staticmethod
    def _default_rules() -> List[AnomalyRule]:
        return [
            AnomalyRule("sudden_change", "1.0.1.8", "sudden_change", {"threshold_pct": 50.0}),
            AnomalyRule("energy_decrease", "1.0.1.8", "sudden_change", {"threshold_pct": -0.01}),
            AnomalyRule("zero_voltage", "1.0.32.7", "out_of_range", {"min_val": 180}),
            AnomalyRule("over_voltage", "1.0.32.7", "out_of_range", {"max_val": 260}),
            AnomalyRule("zero_flow", "1.0.1.8", "zero_flow", {"zero_duration_hours": 24}),
        ]

    def add_rule(self, rule: AnomalyRule) -> None:
        self.rules.append(rule)

    def check(self, reading: MeterReading) -> List[AnomalyEvent]:
        """Check a reading against all applicable rules."""
        events = []
        key = f"{reading.meter_id}:{reading.obis_code}"
        history = self._history.setdefault(key, [])

        for rule in self.rules:
            if rule.obis_pattern not in reading.obis_code:
                continue
            event = self._apply_rule(rule, reading, history)
            if event:
                events.append(event)

        # Update history
        try:
            history.append((reading.timestamp, float(reading.value)))
        except (ValueError, TypeError):
            pass

        # Keep last 1000 entries
        if len(history) > 1000:
            self._history[key] = history[-1000:]

        return events

    def _apply_rule(
        self, rule: AnomalyRule, reading: MeterReading,
        history: List[Tuple[str, Any]],
    ) -> Optional[AnomalyEvent]:
        if rule.check_type == "sudden_change":
            return self._check_sudden_change(rule, reading, history)
        elif rule.check_type == "out_of_range":
            return self._check_out_of_range(rule, reading)
        elif rule.check_type == "zero_flow":
            return self._check_zero_flow(rule, reading, history)
        elif rule.check_type == "missing":
            return None  # Missing is detected at schedule level
        return None

    def _check_sudden_change(
        self, rule: AnomalyRule, reading: MeterReading,
        history: List[Tuple[str, Any]],
    ) -> Optional[AnomalyEvent]:
        if not history:
            return None
        try:
            prev_val = float(history[-1][1])
            curr_val = float(reading.value)
            threshold_pct = rule.params.get("threshold_pct", 50.0)
            if prev_val == 0:
                return None
            change_pct = ((curr_val - prev_val) / abs(prev_val)) * 100
            if abs(change_pct) > abs(threshold_pct):
                return AnomalyEvent(
                    meter_id=reading.meter_id,
                    obis_code=reading.obis_code,
                    rule_name=rule.name,
                    value=curr_val,
                    expected=prev_val,
                    severity="critical" if change_pct > 0 else "warning",
                )
        except (ValueError, TypeError):
            pass
        return None

    def _check_out_of_range(
        self, rule: AnomalyRule, reading: MeterReading,
    ) -> Optional[AnomalyEvent]:
        try:
            val = float(reading.value)
            min_val = rule.params.get("min_val", float("-inf"))
            max_val = rule.params.get("max_val", float("inf"))
            if val < min_val or val > max_val:
                return AnomalyEvent(
                    meter_id=reading.meter_id,
                    obis_code=reading.obis_code,
                    rule_name=rule.name,
                    value=val,
                    expected=f"[{min_val}, {max_val}]",
                    severity="critical",
                )
        except (ValueError, TypeError):
            pass
        return None

    def _check_zero_flow(
        self, rule: AnomalyRule, reading: MeterReading,
        history: List[Tuple[str, Any]],
    ) -> Optional[AnomalyEvent]:
        try:
            val = float(reading.value)
            if val == 0 and len(history) >= 2:
                # Check if last N readings are also zero
                recent = history[-rule.params.get("zero_duration_hours", 24):]
                if all(float(v) == 0 for _, v in recent):
                    return AnomalyEvent(
                        meter_id=reading.meter_id,
                        obis_code=reading.obis_code,
                        rule_name=rule.name,
                        value=0,
                        expected="non-zero",
                        severity="warning",
                    )
        except (ValueError, TypeError):
            pass
        return None


class CollectionScheduler:
    """Simple scheduled data collection."""

    def __init__(
        self,
        read_func: Callable[[str, List[str]], List[MeterReading]],
        storage: DataStorage,
        anomaly_detector: Optional[AnomalyDetector] = None,
    ):
        """
        Args:
            read_func: Callable(meter_id, obis_list) -> List[MeterReading]
            storage: Storage backend
            anomaly_detector: Optional anomaly detector
        """
        self.read_func = read_func
        self.storage = storage
        self.anomaly_detector = anomaly_detector or AnomalyDetector()
        self._tasks: List[CollectionTask] = []
        self._anomaly_events: List[AnomalyEvent] = []

    def add_task(self, task: CollectionTask) -> None:
        self._tasks.append(task)

    def add_meter(self, meter_id: str, obis_list: List[str], **kwargs) -> None:
        self._tasks.append(CollectionTask(
            meter_id=meter_id, obis_list=obis_list, **kwargs
        ))

    def collect_all(self) -> List[MeterReading]:
        """Execute collection for all enabled tasks."""
        all_readings = []
        for task in self._tasks:
            if not task.enabled:
                continue
            readings = self._collect_task(task)
            all_readings.extend(readings)

        # Store all
        self.storage.store_batch(all_readings)

        # Check anomalies
        for reading in all_readings:
            events = self.anomaly_detector.check(reading)
            self._anomaly_events.extend(events)

        return all_readings

    def _collect_task(self, task: CollectionTask) -> List[MeterReading]:
        """Collect data for a single task with retry."""
        for attempt in range(task.retry_count):
            try:
                readings = self.read_func(task.meter_id, task.obis_list)
                LOG.info(
                    "Collection success",
                    meter_id=task.meter_id,
                    readings=len(readings),
                    attempt=attempt + 1,
                )
                return readings
            except Exception as e:
                LOG.warning(
                    "Collection failed",
                    meter_id=task.meter_id,
                    attempt=attempt + 1,
                    error=str(e),
                )
                if attempt == task.retry_count - 1:
                    # Generate missing readings
                    return [
                        MeterReading(
                            meter_id=task.meter_id,
                            obis_code=obis,
                            value=None,
                            status="timeout",
                        )
                        for obis in task.obis_list
                    ]
        return []

    def get_anomalies(self) -> List[AnomalyEvent]:
        return self._anomaly_events

    def generate_report(self) -> str:
        """Generate a text collection report."""
        lines = [
            f"=== DLMS Collection Report ===",
            f"Generated: {datetime.now().isoformat()}",
            f"",
            f"Tasks: {len(self._tasks)}",
            f"  Enabled: {sum(1 for t in self._tasks if t.enabled)}",
            f"  Disabled: {sum(1 for t in self._tasks if not t.enabled)}",
            f"",
            f"Anomalies detected: {len(self._anomaly_events)}",
        ]
        for event in self._anomaly_events[-20:]:
            lines.append(
                f"  [{event.severity}] {event.meter_id} {event.obis_code}: "
                f"{event.rule_name} (value={event.value}, expected={event.expected})"
            )
        return "\n".join(lines)
