"""DLMS Data Analytics.

Provides load curve analysis, power quality analysis, tariff calculation,
usage behavior analysis, and abnormal usage detection.
"""
import math
import structlog
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple

LOG = structlog.get_logger()


@dataclass
class LoadCurvePoint:
    """Single point in a load curve."""
    timestamp: str
    value: float
    quality: int = 0  # 0=good, 1=suspect, 2=bad


@dataclass
class LoadCurveResult:
    """Load curve analysis result."""
    peak_kw: float = 0.0
    peak_time: str = ""
    valley_kw: float = float("inf")
    valley_time: str = ""
    average_kw: float = 0.0
    load_factor: float = 0.0  # average/peak ratio
    total_energy_kwh: float = 0.0
    points: int = 0
    min_kw: float = float("inf")
    max_kw: float = 0.0
    std_dev: float = 0.0


@dataclass
class PowerQualityResult:
    """Power quality analysis result."""
    thd_voltage_pct: Optional[float] = None  # Total Harmonic Distortion
    thd_current_pct: Optional[float] = None
    voltage_unbalance_pct: Optional[float] = None
    current_unbalance_pct: Optional[float] = None
    power_factor_avg: Optional[float] = None
    power_factor_min: Optional[float] = None
    frequency_avg_hz: Optional[float] = None
    frequency_deviation_hz: Optional[float] = None
    voltage_dip_count: int = 0
    voltage_swell_count: int = 0
    overvoltage_count: int = 0
    undervoltage_count: int = 0


@dataclass
class TariffResult:
    """Tariff calculation result."""
    total_cost: float = 0.0
    breakdown: Dict[str, float] = field(default_factory=dict)  # tariff -> cost
    energy_by_tariff: Dict[str, float] = field(default_factory=dict)
    demand_charge: float = 0.0
    power_factor_penalty: float = 0.0


@dataclass
class UsageBehaviorResult:
    """Usage behavior analysis result."""
    weekday_avg_kwh: float = 0.0
    weekend_avg_kwh: float = 0.0
    peak_hour_avg_kw: float = 0.0
    offpeak_hour_avg_kw: float = 0.0
    seasonal_comparison: Dict[str, float] = field(default_factory=dict)
    daily_pattern: Dict[int, float] = field(default_factory=dict)  # hour -> avg kw


@dataclass
class AbnormalUsageEvent:
    """Abnormal usage detection event."""
    event_type: str  # theft, leak, abnormal_increase, unusual_pattern
    start_time: str
    end_time: str
    severity: str  # low, medium, high, critical
    description: str
    value: Optional[float] = None
    expected_range: Optional[Tuple[float, float]] = None


class LoadCurveAnalyzer:
    """Analyzes load curve data for a meter."""

    def analyze(self, points: List[LoadCurvePoint]) -> LoadCurveResult:
        """Perform load curve analysis."""
        if not points:
            return LoadCurveResult()

        values = [p.value for p in points]
        n = len(values)

        result = LoadCurveResult(points=n)
        result.max_kw = max(values)
        result.min_kw = min(values)
        result.peak_kw = max(values)
        result.valley_kw = min(values)
        result.average_kw = sum(values) / n

        # Find peak and valley times
        for p in points:
            if p.value == result.peak_kw and not result.peak_time:
                result.peak_time = p.timestamp
            if p.value == result.valley_kw and not result.valley_time:
                result.valley_time = p.timestamp

        # Load factor = average / peak
        if result.peak_kw > 0:
            result.load_factor = result.average_kw / result.peak_kw

        # Total energy (trapezoidal integration for interval data)
        if n >= 2:
            interval_hours = self._estimate_interval_hours(points)
            # Sum of average of consecutive values * interval
            total = 0.0
            for i in range(n - 1):
                total += (values[i] + values[i + 1]) / 2
            result.total_energy_kwh = total * interval_hours

        # Standard deviation
        if n > 1:
            mean = result.average_kw
            variance = sum((v - mean) ** 2 for v in values) / (n - 1)
            result.std_dev = math.sqrt(variance)

        return result

    @staticmethod
    def _estimate_interval_hours(points: List[LoadCurvePoint]) -> float:
        """Estimate the time interval between load curve points."""
        if len(points) < 2:
            return 1.0  # default 1 hour
        try:
            t1 = datetime.fromisoformat(points[0].timestamp)
            t2 = datetime.fromisoformat(points[1].timestamp)
            delta = (t2 - t1).total_seconds() / 3600
            return max(delta, 0.001)  # avoid zero
        except (ValueError, IndexError):
            return 1.0

    def detect_peaks(self, points: List[LoadCurvePoint], threshold_pct: float = 80.0) -> List[LoadCurvePoint]:
        """Find load peaks above threshold percentage of maximum."""
        if not points:
            return []
        max_val = max(p.value for p in points)
        threshold = max_val * threshold_pct / 100
        return [p for p in points if p.value >= threshold]


class PowerQualityAnalyzer:
    """Analyzes power quality metrics."""

    def analyze(
        self,
        voltages: Optional[Dict[str, List[float]]] = None,  # phase -> values
        currents: Optional[Dict[str, List[float]]] = None,
        power_factors: Optional[List[float]] = None,
        frequencies: Optional[List[float]] = None,
    ) -> PowerQualityResult:
        """Perform power quality analysis."""
        result = PowerQualityResult()

        # Voltage analysis
        if voltages:
            result.voltage_unbalance_pct = self._calculate_unbalance(voltages)
            va = voltages.get("A", voltages.get("a", []))
            if va:
                nominal = 220.0  # China standard
                result.overvoltage_count = sum(1 for v in va if v > nominal * 1.07)
                result.undervoltage_count = sum(1 for v in va if v < nominal * 0.90)
                # Voltage dips (< 90% for short duration)
                for i in range(1, len(va)):
                    if va[i] < nominal * 0.90 and va[i-1] >= nominal * 0.90:
                        result.voltage_dip_count += 1
                    if va[i] > nominal * 1.10 and va[i-1] <= nominal * 1.10:
                        result.voltage_swell_count += 1

        # Current analysis
        if currents:
            result.current_unbalance_pct = self._calculate_unbalance(currents)

        # Power factor
        if power_factors:
            result.power_factor_avg = sum(power_factors) / len(power_factors)
            result.power_factor_min = min(power_factors)

        # Frequency
        if frequencies:
            result.frequency_avg_hz = sum(frequencies) / len(frequencies)
            nominal_freq = 50.0
            result.frequency_deviation_hz = abs(result.frequency_avg_hz - nominal_freq)

        return result

    @staticmethod
    def _calculate_unbalance(phase_values: Dict[str, List[float]]) -> float:
        """Calculate voltage/current unbalance per IEC 61000-4-30."""
        phase_avgs = {k: (sum(v) / len(v) if v else 0) for k, v in phase_values.items()}
        avgs = list(phase_avgs.values())
        if len(avgs) < 3:
            return 0.0
        avg = sum(avgs) / len(avgs)
        if avg == 0:
            return 0.0
        max_dev = max(abs(v - avg) for v in avgs)
        return (max_dev / avg) * 100

    def calculate_thd(self, harmonics: List[float], fundamental: float) -> float:
        """Calculate Total Harmonic Distortion (THD).

        Args:
            harmonics: List of harmonic component magnitudes (H2, H3, ...)
            fundamental: Fundamental component magnitude (H1)
        """
        if not harmonics or fundamental == 0:
            return 0.0
        sum_sq = sum(h ** 2 for h in harmonics)
        return (math.sqrt(sum_sq) / fundamental) * 100


class TariffCalculator:
    """Calculates electricity costs with support for TOU and tiered tariffs."""

    def __init__(
        self,
        tou_rates: Optional[Dict[str, float]] = None,
        tiers: Optional[List[Tuple[float, float]]] = None,
        demand_rate: float = 0.0,
    ):
        """
        Args:
            tou_rates: Time-of-use rates dict. Keys: 'peak', 'flat', 'valley'
            tiers: List of (threshold_kwh, rate_yuan_kwh) for tiered pricing
            demand_rate: Demand charge per kW
        """
        self.tou_rates = tou_rates or {
            "peak": 1.05,    # 尖峰
            "high": 0.85,    # 高峰
            "flat": 0.55,    # 平段
            "valley": 0.30,  # 低谷
        }
        self.tiers = tiers or [
            (0, 0.52),       # 0-170 kWh
            (170, 0.57),     # 170-260 kWh
            (260, 0.82),     # >260 kWh
        ]
        self.demand_rate = demand_rate

    def calculate_tou(
        self, energy_by_period: Dict[str, float], max_demand_kw: float = 0.0
    ) -> TariffResult:
        """Calculate cost using time-of-use rates.

        Args:
            energy_by_period: dict with keys 'peak', 'high', 'flat', 'valley'
            max_demand_kw: Maximum demand for demand charge
        """
        result = TariffResult()
        for period, energy in energy_by_period.items():
            rate = self.tou_rates.get(period, self.tou_rates.get("flat", 0.55))
            cost = energy * rate
            result.breakdown[period] = round(cost, 2)
            result.energy_by_tariff[period] = energy
            result.total_cost += cost
        if max_demand_kw > 0 and self.demand_rate > 0:
            result.demand_charge = max_demand_kw * self.demand_rate
            result.total_cost += result.demand_charge
        result.total_cost = round(result.total_cost, 2)
        return result

    def calculate_tiered(self, total_kwh: float) -> TariffResult:
        """Calculate cost using tiered/stepped pricing."""
        result = TariffResult()
        remaining = total_kwh
        prev_threshold = 0
        for threshold, rate in self.tiers:
            if remaining <= 0:
                break
            band = min(remaining, threshold - prev_threshold)
            if band <= 0:
                prev_threshold = threshold
                continue
            cost = band * rate
            result.breakdown[f"tier_{len(result.breakdown)+1}"] = round(cost, 2)
            result.total_cost += cost
            remaining -= band
            prev_threshold = threshold
        result.total_cost = round(result.total_cost, 2)
        return result

    def power_factor_penalty(self, pf: float) -> float:
        """Calculate power factor penalty/reward.

        China standard: PF >= 0.90 is normal.
        Below 0.90: penalty of (0.90 - PF) * 2% per 0.01 below.
        Above 0.95: reward of 0.75% per 0.01 above.
        """
        if pf >= 0.95:
            return -((pf - 0.95) * 100 * 0.0075)  # negative = reward
        elif pf < 0.90:
            return ((0.90 - pf) * 100 * 0.02)
        return 0.0


class UsageBehaviorAnalyzer:
    """Analyzes electricity usage behavior patterns."""

    def analyze(
        self,
        hourly_data: Dict[str, float],  # "YYYY-MM-DD HH:MM" -> kWh
    ) -> UsageBehaviorResult:
        """Analyze usage behavior from timestamped consumption data."""
        result = UsageBehaviorResult()

        weekday_values: List[float] = []
        weekend_values: List[float] = []
        peak_values: List[float] = []  # 10:00-12:00, 18:00-22:00
        offpeak_values: List[float] = []  # 23:00-7:00
        hourly_sums: Dict[int, List[float]] = defaultdict(list)
        seasonal: Dict[str, List[float]] = defaultdict(list)

        for ts, value in hourly_data.items():
            try:
                dt = datetime.fromisoformat(ts)
            except ValueError:
                continue

            # Weekday vs weekend
            if dt.weekday() < 5:
                weekday_values.append(value)
            else:
                weekend_values.append(value)

            # Peak vs off-peak
            hour = dt.hour
            if 10 <= hour < 12 or 18 <= hour < 22:
                peak_values.append(value)
            elif hour >= 23 or hour < 7:
                offpeak_values.append(value)

            # Hourly pattern
            hourly_sums[hour].append(value)

            # Seasonal
            month = dt.strftime("%Y-%m")
            seasonal[month].append(value)

        if weekday_values:
            result.weekday_avg_kwh = sum(weekday_values) / len(weekday_values)
        if weekend_values:
            result.weekend_avg_kwh = sum(weekend_values) / len(weekend_values)
        if peak_values:
            result.peak_hour_avg_kw = sum(peak_values) / len(peak_values)
        if offpeak_values:
            result.offpeak_hour_avg_kw = sum(offpeak_values) / len(offpeak_values)

        # Hourly pattern
        for hour, values in hourly_sums.items():
            result.daily_pattern[hour] = round(sum(values) / len(values), 3)

        # Seasonal
        for month, values in seasonal.items():
            result.seasonal_comparison[month] = round(sum(values), 2)

        return result


class AbnormalUsageDetector:
    """Detects abnormal electricity usage patterns."""

    def __init__(
        self,
        sudden_change_threshold: float = 100.0,  # % change
        zero_threshold_hours: int = 48,
        min_data_points: int = 7,
    ):
        self.sudden_change_threshold = sudden_change_threshold
        self.zero_threshold_hours = zero_threshold_hours
        self.min_data_points = min_data_points

    def detect(
        self,
        daily_data: Dict[str, float],  # "YYYY-MM-DD" -> daily kWh
        expected_range: Optional[Tuple[float, float]] = None,
    ) -> List[AbnormalUsageEvent]:
        """Detect abnormal usage patterns."""
        events: List[AbnormalUsageEvent] = []
        sorted_days = sorted(daily_data.keys())

        if len(sorted_days) < self.min_data_points:
            return events

        values = [daily_data[d] for d in sorted_days]

        # Calculate statistics
        avg = sum(values) / len(values)
        if len(values) > 1:
            std = math.sqrt(sum((v - avg) ** 2 for v in values) / (len(values) - 1))
        else:
            std = 0

        # Detect sudden changes
        for i in range(1, len(values)):
            prev = values[i - 1]
            curr = values[i]
            if prev > 0:
                change_pct = ((curr - prev) / prev) * 100
                if abs(change_pct) > self.sudden_change_threshold:
                    severity = "critical" if change_pct > 0 else "medium"
                    events.append(AbnormalUsageEvent(
                        event_type="abnormal_increase" if change_pct > 0 else "abnormal_decrease",
                        start_time=sorted_days[i],
                        end_time=sorted_days[i],
                        severity=severity,
                        description=f"Sudden {'increase' if change_pct > 0 else 'decrease'} "
                                    f"of {abs(change_pct):.1f}%",
                        value=curr,
                        expected_range=(prev * 0.5, prev * 1.5),
                    ))

        # Detect zero consumption - check at end too
        zero_days = []
        for i, (day, val) in enumerate(zip(sorted_days, values)):
            if val == 0 or val is None:
                zero_days.append(i)
            else:
                if len(zero_days) >= max(1, self.zero_threshold_hours // 24):
                    events.append(AbnormalUsageEvent(
                        event_type="zero_consumption",
                        start_time=sorted_days[zero_days[0]],
                        end_time=sorted_days[zero_days[-1]],
                        severity="high",
                        description=f"Zero consumption for {len(zero_days)} consecutive days",
                    ))
                zero_days = []
        # Check remaining zero streak
        if len(zero_days) >= max(1, self.zero_threshold_hours // 24):
            events.append(AbnormalUsageEvent(
                event_type="zero_consumption",
                start_time=sorted_days[zero_days[0]],
                end_time=sorted_days[zero_days[-1]],
                severity="high",
                description=f"Zero consumption for {len(zero_days)} consecutive days",
            ))

        # Detect usage outside expected range
        if expected_range:
            low, high = expected_range
            for day, val in zip(sorted_days, values):
                if val < low or val > high:
                    events.append(AbnormalUsageEvent(
                        event_type="unusual_pattern",
                        start_time=day,
                        end_time=day,
                        severity="medium",
                        description=f"Usage {val} outside expected range [{low}, {high}]",
                        value=val,
                        expected_range=expected_range,
                    ))

        return events
