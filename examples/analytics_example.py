"""Example: DLMS Data Analytics

Demonstrates load curve analysis, power quality, tariff calculation,
and abnormal usage detection.
"""
from dlms_cosem.analytics import (
    LoadCurvePoint, LoadCurveAnalyzer,
    PowerQualityAnalyzer,
    TariffCalculator,
    UsageBehaviorAnalyzer,
    AbnormalUsageDetector,
)


def main():
    # === Load Curve Analysis ===
    print("=" * 50)
    print("LOAD CURVE ANALYSIS")
    print("=" * 50)

    points = [
        LoadCurvePoint(f"2026-01-15T{h:02d}:00:00", v)
        for h, v in enumerate([
            2.1, 1.8, 1.5, 1.3, 1.4, 2.0, 4.5, 6.2,  # 00-07
            7.8, 8.5, 9.1, 8.8, 7.5, 7.2, 6.8, 7.5,  # 08-15
            8.2, 9.5, 10.2, 9.8, 8.5, 7.0, 4.5, 2.8,  # 16-23
        ])
    ]

    analyzer = LoadCurveAnalyzer()
    result = analyzer.analyze(points)
    print(f"  Peak:     {result.peak_kw:.1f} kW at {result.peak_time}")
    print(f"  Valley:   {result.valley_kw:.1f} kW at {result.valley_time}")
    print(f"  Average:  {result.average_kw:.1f} kW")
    print(f"  Load Factor: {result.load_factor:.2%}")
    print(f"  Std Dev:  {result.std_dev:.2f} kW")

    # === Power Quality ===
    print("\n" + "=" * 50)
    print("POWER QUALITY ANALYSIS")
    print("=" * 50)

    pq = PowerQualityAnalyzer()
    pq_result = pq.analyze(
        voltages={"A": [220, 221, 219, 250, 220], "B": [220, 220, 220], "C": [220, 219, 221]},
        power_factors=[0.95, 0.92, 0.98, 0.89],
        frequencies=[50.01, 49.99, 50.00, 50.02],
    )
    print(f"  Voltage Unbalance:  {pq_result.voltage_unbalance_pct:.2f}%")
    print(f"  Power Factor Avg:   {pq_result.power_factor_avg:.3f}")
    print(f"  Power Factor Min:   {pq_result.power_factor_min:.3f}")
    print(f"  Frequency Avg:      {pq_result.frequency_avg_hz:.3f} Hz")
    print(f"  Overvoltage Count:  {pq_result.overvoltage_count}")
    print(f"  THD example:        {pq.calculate_thd([5.0, 3.0, 2.0], 220):.2f}%")

    # === Tariff Calculation ===
    print("\n" + "=" * 50)
    print("TARIFF CALCULATION (China TOU)")
    print("=" * 50)

    calc = TariffCalculator()
    tou_result = calc.calculate_tou({
        "peak": 150,    # kWh at peak rate
        "high": 200,    # kWh at high rate
        "flat": 300,    # kWh at flat rate
        "valley": 100,  # kWh at valley rate
    }, max_demand_kw=50)

    print(f"  Total Cost:        ¥{tou_result.total_cost:.2f}")
    for period, cost in tou_result.breakdown.items():
        print(f"    {period}: ¥{cost:.2f}")
    print(f"  Demand Charge:     ¥{tou_result.demand_charge:.2f}")

    # Power factor penalty
    pf_penalty = calc.power_factor_penalty(0.85)
    print(f"  PF Penalty (0.85): {pf_penalty:+.2%}")

    # === Abnormal Usage Detection ===
    print("\n" + "=" * 50)
    print("ABNORMAL USAGE DETECTION")
    print("=" * 50)

    detector = AbnormalUsageDetector(sudden_change_threshold=50)
    daily_data = {f"2026-01-{i+1:02d}": v for i, v in enumerate([
        10, 11, 10, 12, 11, 10, 11, 10, 25, 10  # Day 9 has 150% spike
    ])}
    events = detector.detect(daily_data)
    if events:
        for e in events:
            print(f"  [{e.severity}] {e.event_type} on {e.start_time}: {e.description}")
    else:
        print("  No anomalies detected.")


if __name__ == "__main__":
    main()
