"""Tests for China GB/T 17215.301 extensions."""
import pytest

from dlms_cosem.china_gb import (
    GBTariffType, GBTimeSeason, GBCp28Command, GBPhase,
    GBTariffSchedule, GBTariffProfile, GBRS485Config,
    GBCp28Frame, GBTariffMapper, GBMeter,
)


class TestGBTariffSchedule:
    def test_duration(self):
        sched = GBTariffSchedule(
            tariff_type=GBTariffType.PEAK,
            hour_start=8, minute_start=0,
            hour_end=11, minute_end=0,
        )
        assert sched.duration_minutes == 180

    def test_duration_cross_hour(self):
        sched = GBTariffSchedule(
            tariff_type=GBTariffType.FLAT,
            hour_start=23, minute_start=30,
            hour_end=1, minute_end=0,
        )
        # 60 - 30 + 60 = 90 minutes
        assert sched.duration_minutes == 90


class TestGBTariffProfile:
    def test_add_and_get(self):
        profile = GBTariffProfile()
        profile.add_schedule(GBTariffSchedule(
            tariff_type=GBTariffType.PEAK,
            hour_start=8, minute_start=0,
            hour_end=11, minute_end=0,
            season=GBTimeSeason.SUMMER,
        ))
        tariff = profile.get_current_tariff(9, 0, GBTimeSeason.SUMMER)
        assert tariff == GBTariffType.PEAK

    def test_default_flat(self):
        profile = GBTariffProfile()
        tariff = profile.get_current_tariff(12, 0, GBTimeSeason.SPRING)
        assert tariff == GBTariffType.FLAT

    def test_all_seasons(self):
        profile = GBTariffProfile()
        profile.add_schedule(GBTariffSchedule(
            tariff_type=GBTariffType.VALLEY,
            hour_start=23, minute_start=0,
            hour_end=7, minute_end=0,
            season=GBTimeSeason.WINTER,
        ))
        seasons = profile.get_all_seasons()
        assert GBTimeSeason.WINTER in seasons


class TestGBRS485Config:
    def test_default(self):
        cfg = GBRS485Config()
        assert cfg.baud_rate == 2400
        assert cfg.parity == "even"
        assert cfg.address_length == 12

    def test_serial_config(self):
        assert GBRS485Config().serial_config == "2400,8,E,1"

    def test_parity_char(self):
        assert GBRS485Config(parity="even").parity_char == "E"
        assert GBRS485Config(parity="odd").parity_char == "O"
        assert GBRS485Config(parity="none").parity_char == "N"

    def test_from_string(self):
        cfg = GBRS485Config.from_string("9600,8,N,1")
        assert cfg.baud_rate == 9600
        assert cfg.parity == "none"
        assert cfg.stop_bits == 1


class TestGBCp28Frame:
    def test_encode_decode(self):
        frame = GBCp28Frame(
            address=b"123456",
            command=GBCp28Command.READ_DATA,
            data=b"\x00\x01\x02",
        )
        encoded = frame.to_bytes()

        assert encoded[0] == 0x68  # Start
        assert encoded[-1] == 0x16  # End

        decoded = GBCp28Frame.from_bytes(encoded)
        assert decoded.address == b"123456"
        assert decoded.command == GBCp28Command.READ_DATA
        assert decoded.data == b"\x00\x01\x02"

    def test_invalid_frame(self):
        with pytest.raises(ValueError, match="Invalid CP 28"):
            GBCp28Frame.from_bytes(b"INVALID")


class TestGBTariffMapper:
    def test_get_obis_name(self):
        assert GBTariffMapper.get_obis_name("1.0.1.8.0.0") == "Peak Active Energy Import"
        assert GBTariffMapper.get_obis_name("1.0.31.7.0.0") == "Voltage Phase A"
        assert GBTariffMapper.get_obis_name("unknown") == "Unknown"

    def test_get_energy_obis(self):
        assert GBTariffMapper.get_energy_obis(1, GBTariffType.PEAK) == "1.0.1.8.0.0"
        assert GBTariffMapper.get_energy_obis(1, GBTariffType.VALLEY) == "1.0.4.8.0.0"

    def test_get_voltage_obis(self):
        assert GBTariffMapper.get_voltage_obis(GBPhase.PHASE_A) == "1.0.31.7.0.0"
        assert GBTariffMapper.get_voltage_obis(GBPhase.PHASE_B) == "1.0.52.7.0.0"
        assert GBTariffMapper.get_voltage_obis(GBPhase.PHASE_C) == "1.0.73.7.0.0"

    def test_get_current_obis(self):
        assert GBTariffMapper.get_current_obis(GBPhase.PHASE_A) == "1.0.51.5.0.0"

    def test_get_demand_obis(self):
        assert GBTariffMapper.get_demand_obis(GBTariffType.TOTAL) == "1.0.0.1.0.0"

    def test_parse_obis_code(self):
        result = GBTariffMapper.parse_obis_code("1.0.1.8.0.0")
        assert result["group_a"] == 1
        assert result["group_c"] == 1
        assert result["name"] == "Peak Active Energy Import"

    def test_parse_invalid_obis(self):
        result = GBTariffMapper.parse_obis_code("invalid")
        assert "error" in result


class TestGBMeter:
    def test_create_meter(self):
        meter = GBMeter("123456789012")
        assert meter.address == "123456789012"

    def test_registers(self):
        meter = GBMeter()
        meter.write_register("1.0.0.8.0.0", 12345.6)
        assert meter.read_register("1.0.0.8.0.0") == 12345.6
        assert meter.read_register("nonexistent") is None

    def test_create_cp28_frame(self):
        meter = GBMeter("ABCDEF")
        frame = meter.create_cp28_frame(GBCp28Command.READ_DATA)
        assert isinstance(frame, GBCp28Frame)
        assert frame.command == GBCp28Command.READ_DATA

    def test_standard_tariff(self):
        meter = GBMeter()
        meter.setup_china_standard_tariff()
        # Peak at 9:00
        assert meter.tariff_profile.get_current_tariff(9, 0, GBTimeSeason.SUMMER) == GBTariffType.PEAK
        # Valley at 3:00
        assert meter.tariff_profile.get_current_tariff(3, 0, GBTimeSeason.WINTER) == GBTariffType.VALLEY
        # Shoulder at 7:30
        assert meter.tariff_profile.get_current_tariff(7, 30, GBTimeSeason.SPRING) == GBTariffType.SHOULDER

    def test_enums(self):
        assert GBTariffType.PEAK == 1
        assert GBTariffType.VALLEY == 4
        assert GBTimeSeason.SUMMER == 1
        assert GBCp28Command.READ_DATA == 0x01
        assert GBCp28Command.RELAY_CONTROL == 0x10


class TestGBTariffMapperExtensions:
    def test_gb_obis_count(self):
        # Should have comprehensive China OBIS extensions
        assert len(GBTariffMapper.GB_OBIS_EXTENSIONS) > 15

    def test_frequency_obis(self):
        assert "1.0.14.7.0.0" in GBTariffMapper.GB_OBIS_EXTENSIONS

    def test_power_factor_obis(self):
        assert "1.0.80.82.0.0" in GBTariffMapper.GB_OBIS_EXTENSIONS
