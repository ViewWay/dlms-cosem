"""Example: DLMS Data Collection Automation

Demonstrates batch meter reading, anomaly detection, and report generation.
"""
from dlms_cosem.automation import (
    MeterReading, CollectionScheduler, InMemoryStorage,
    SqliteStorage, AnomalyDetector, AnomalyRule,
)


def mock_read_func(meter_id, obis_list):
    """Simulate reading from a meter."""
    import random
    readings = []
    for obis in obis_list:
        readings.append(MeterReading(
            meter_id=meter_id,
            obis_code=obis,
            value=round(random.uniform(100, 200), 2),
            unit="kWh",
        ))
    return readings


def main():
    # Use SQLite for persistent storage
    storage = SqliteStorage("meter_data.db")

    # Create scheduler with anomaly detection
    detector = AnomalyDetector([
        AnomalyRule("sudden_spike", "1.0.1.8", "sudden_change", {"threshold_pct": 80}),
        AnomalyRule("low_voltage", "1.0.32.7", "out_of_range", {"min_val": 180}),
    ])
    scheduler = CollectionScheduler(mock_read_func, storage, detector)

    # Add meters to monitor
    scheduler.add_meter("METER_001", [
        "1.0.1.8.0.255",  # Total import active energy
        "1.0.32.7.0.255",  # Voltage phase A
        "1.0.31.7.0.255",  # Current phase A
        "1.0.11.7.0.255",  # Active power total
    ])
    scheduler.add_meter("METER_002", [
        "1.0.1.8.0.255",
        "1.0.32.7.0.255",
    ])

    # Collect from all meters
    readings = scheduler.collect_all()
    print(f"Collected {len(readings)} readings")

    # Check for anomalies
    anomalies = scheduler.get_anomalies()
    if anomalies:
        print(f"\n⚠️  {len(anomalies)} anomalies detected:")
        for a in anomalies:
            print(f"  [{a.severity}] {a.meter_id} {a.obis_code}: {a.rule_name}")
    else:
        print("No anomalies detected.")

    # Generate report
    print("\n" + scheduler.generate_report())

    # Query historical data
    history = storage.query("METER_001", obis="1.0.1.8")
    print(f"\nHistorical readings for METER_001 energy: {len(history)} records")

    storage.close()


if __name__ == "__main__":
    main()
