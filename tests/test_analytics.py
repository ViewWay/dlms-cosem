"""Tests for DLMS Analytics."""
import math
import pytest
from dlms_cosem.analytics import (
    LoadCurvePoint, LoadCurveAnalyzer, PowerQualityAnalyzer,
    TariffCalculator, UsageBehaviorAnalyzer, AbnormalUsageDetector,
    LoadCurveResult, PowerQualityResult, TariffResult,
    UsageBehaviorResult, AbnormalUsageEvent,
)


class TestLoadCurveAnalyzer:
    def _make_points(self, values):
        return [LoadCurvePoint(f"2026-01-{i+1:02d}T{h:02d}:00:00", v)
                for i, (h, v) in enumerate(values)]

    def test_basic_analysis(self):
        analyzer = LoadCurveAnalyzer()
        points = self._make_points([
            (0, 10), (1, 8), (2, 6), (3, 5), (4, 7), (5, 12), (6, 15), (7, 20),
        ])
        result = analyzer.analyze(points)
        assert result.points == 8
        assert result.max_kw == 20
        assert result.min_kw == 5
        assert result.peak_kw == 20
        assert result.valley_kw == 5
        assert 0 < result.average_kw < 20
        assert 0 < result.load_factor <= 1.0

    def test_empty_data(self):
        analyzer = LoadCurveAnalyzer()
        result = analyzer.analyze([])
        assert result.points == 0

    def test_single_point(self):
        analyzer = LoadCurveAnalyzer()
        result = analyzer.analyze([LoadCurvePoint("t1", 100)])
        assert result.points == 1
        assert result.peak_kw == 100
        assert result.valley_kw == 100

    def test_std_deviation(self):
        analyzer = LoadCurveAnalyzer()
        points = [LoadCurvePoint(f"t{i}", float(i * 10)) for i in range(10)]
        result = analyzer.analyze(points)
        assert result.std_dev > 0

    def test_detect_peaks(self):
        analyzer = LoadCurveAnalyzer()
        points = [LoadCurvePoint(f"t{i}", float(v))
                  for i, v in enumerate([10, 20, 30, 100, 95, 10, 20])]
        peaks = analyzer.detect_peaks(points, threshold_pct=80)
        assert len(peaks) >= 1


class TestPowerQualityAnalyzer:
    def test_voltage_unbalance(self):
        analyzer = PowerQualityAnalyzer()
        result = analyzer.analyze(voltages={
            "A": [220, 221, 219],
            "B": [220, 220, 220],
            "C": [220, 219, 221],
        })
        assert result.voltage_unbalance_pct is not None
        assert result.voltage_unbalance_pct >= 0

    def test_overvoltage_count(self):
        analyzer = PowerQualityAnalyzer()
        result = analyzer.analyze(voltages={
            "A": [220, 250, 220, 260, 220],  # 2 overvoltage
        })
        assert result.overvoltage_count == 2

    def test_undervoltage_count(self):
        analyzer = PowerQualityAnalyzer()
        result = analyzer.analyze(voltages={
            "A": [220, 190, 220, 170, 220],  # 2 undervoltage (< 198V)
        })
        assert result.undervoltage_count == 2

    def test_power_factor(self):
        analyzer = PowerQualityAnalyzer()
        result = analyzer.analyze(power_factors=[0.95, 0.92, 0.98])
        assert result.power_factor_avg is not None
        assert result.power_factor_min == 0.92

    def test_frequency(self):
        analyzer = PowerQualityAnalyzer()
        result = analyzer.analyze(frequencies=[50.01, 49.99, 50.00])
        assert abs(result.frequency_avg_hz - 50.0) < 0.1

    def test_thd(self):
        analyzer = PowerQualityAnalyzer()
        thd = analyzer.calculate_thd([5.0, 3.0, 2.0], 220.0)
        assert thd > 0
        # THD = sqrt(25+9+4)/220 * 100 ≈ 3.2%
        assert 2.5 < thd < 3.5

    def test_thd_zero_harmonics(self):
        analyzer = PowerQualityAnalyzer()
        assert analyzer.calculate_thd([], 220) == 0.0


class TestTariffCalculator:
    def test_tou_calculation(self):
        calc = TariffCalculator()
        result = calc.calculate_tou({
            "peak": 100, "flat": 200, "valley": 50,
        })
        assert result.total_cost > 0
        assert "peak" in result.breakdown
        assert result.energy_by_tariff["peak"] == 100

    def test_tou_with_demand(self):
        calc = TariffCalculator(demand_rate=30.0)
        result = calc.calculate_tou({"flat": 100}, max_demand_kw=50)
        assert result.demand_charge == 1500.0

    def test_tiered_pricing(self):
        calc = TariffCalculator()
        result = calc.calculate_tiered(300)  # crosses all 3 tiers
        assert result.total_cost > 0
        assert len(result.breakdown) >= 2

    def test_tiered_first_tier(self):
        calc = TariffCalculator()
        result = calc.calculate_tiered(100)  # Only first tier
        assert len(result.breakdown) == 1

    def test_power_factor_penalty_low(self):
        calc = TariffCalculator()
        penalty = calc.power_factor_penalty(0.85)  # Below 0.90
        assert penalty > 0

    def test_power_factor_reward(self):
        calc = TariffCalculator()
        reward = calc.power_factor_penalty(0.97)  # Above 0.95
        assert reward < 0  # Negative = reward

    def test_power_factor_normal(self):
        calc = TariffCalculator()
        assert calc.power_factor_penalty(0.92) == 0.0


class TestUsageBehaviorAnalyzer:
    def test_basic_analysis(self):
        analyzer = UsageBehaviorAnalyzer()
        # Weekday data
        data = {
            "2026-01-05T10:00:00": 5.0,  # Monday (weekday, peak)
            "2026-01-05T02:00:00": 2.0,  # Monday (off-peak)
            "2026-01-06T10:00:00": 6.0,  # Tuesday
            "2026-01-11T10:00:00": 3.0,  # Sunday (weekend)
        }
        result = analyzer.analyze(data)
        assert result.weekday_avg_kwh > 0
        assert result.weekend_avg_kwh > 0
        assert result.peak_hour_avg_kw > result.offpeak_hour_avg_kw

    def test_empty_data(self):
        analyzer = UsageBehaviorAnalyzer()
        result = analyzer.analyze({})
        assert result.weekday_avg_kwh == 0

    def test_daily_pattern(self):
        analyzer = UsageBehaviorAnalyzer()
        data = {f"2026-01-05T{h:02d}:00:00": float(h) for h in range(24)}
        result = analyzer.analyze(data)
        assert len(result.daily_pattern) == 24


class TestAbnormalUsageDetector:
    def test_sudden_increase(self):
        detector = AbnormalUsageDetector(sudden_change_threshold=50)
        daily = {
            "2026-01-01": 10, "2026-01-02": 11, "2026-01-03": 10,
            "2026-01-04": 12, "2026-01-05": 10, "2026-01-06": 11,
            "2026-01-07": 10, "2026-01-08": 10, "2026-01-09": 30,  # 200% jump
        }
        events = detector.detect(daily)
        assert any(e.event_type == "abnormal_increase" for e in events)

    def test_zero_consumption(self):
        detector = AbnormalUsageDetector(zero_threshold_hours=24, min_data_points=3)
        daily = {}
        for i in range(10):
            day = f"2026-01-{i+1:02d}"
            daily[day] = 0 if i >= 3 else 10
        events = detector.detect(daily)
        # 7 consecutive zero days (>= 24h threshold means >= 1 day)
        assert any(e.event_type == "zero_consumption" for e in events)

    def test_expected_range(self):
        detector = AbnormalUsageDetector(min_data_points=3)
        daily = {
            "2026-01-01": 10, "2026-01-02": 11, "2026-01-03": 10,
            "2026-01-04": 100,  # Way above range
        }
        events = detector.detect(daily, expected_range=(5, 20))
        assert any(e.event_type == "unusual_pattern" for e in events)

    def test_insufficient_data(self):
        detector = AbnormalUsageDetector()
        events = detector.detect({"2026-01-01": 10})
        assert len(events) == 0
