"""Tests for timezone utility functions"""

import pytest
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from app.core.utils.timezone import (
    format_timestamp,
    add_hours,
    parse_iso_datetime,
    is_expired,
    TIMEZONE,
)


class TestFormatTimestamp:
    """Tests for format_timestamp()"""

    def test_aware_datetime_formats_correctly(self):
        dt = datetime(2026, 1, 19, 22, 50, 0, tzinfo=TIMEZONE)
        result = format_timestamp(dt)
        assert result == "2026-01-19 22:50:00"

    def test_naive_datetime_gets_timezone_applied(self):
        dt = datetime(2026, 3, 15, 10, 30, 0)  # no tzinfo
        result = format_timestamp(dt)
        assert result == "2026-03-15 10:30:00"

    def test_custom_format(self):
        dt = datetime(2026, 1, 19, 22, 50, 0, tzinfo=TIMEZONE)
        result = format_timestamp(dt, fmt="%d/%m/%Y")
        assert result == "19/01/2026"

    def test_backup_timestamp_format(self):
        dt = datetime(2026, 1, 19, 22, 50, 0, tzinfo=TIMEZONE)
        result = format_timestamp(dt, fmt="%d%m%Y_%H%M%S")
        assert result == "19012026_225000"


class TestAddHours:
    """Tests for add_hours()"""

    def test_add_positive_hours(self):
        dt = datetime(2026, 1, 19, 10, 0, 0, tzinfo=TIMEZONE)
        result = add_hours(dt, 5)
        assert result == datetime(2026, 1, 19, 15, 0, 0, tzinfo=TIMEZONE)

    def test_add_zero_hours_returns_same_time(self):
        dt = datetime(2026, 1, 19, 10, 0, 0, tzinfo=TIMEZONE)
        result = add_hours(dt, 0)
        assert result == dt

    def test_add_negative_hours_subtracts(self):
        dt = datetime(2026, 1, 19, 10, 0, 0, tzinfo=TIMEZONE)
        result = add_hours(dt, -3)
        assert result == datetime(2026, 1, 19, 7, 0, 0, tzinfo=TIMEZONE)

    def test_add_24_hours_advances_day(self):
        dt = datetime(2026, 1, 19, 10, 0, 0, tzinfo=TIMEZONE)
        result = add_hours(dt, 24)
        assert result == datetime(2026, 1, 20, 10, 0, 0, tzinfo=TIMEZONE)


class TestParseIsoDatetime:
    """Tests for parse_iso_datetime()"""

    def test_valid_iso_string_with_timezone(self):
        dt = parse_iso_datetime("2026-01-19T22:50:00+01:00")
        assert dt.year == 2026
        assert dt.month == 1
        assert dt.day == 19
        assert dt.hour == 22
        assert dt.minute == 50

    def test_valid_iso_string_utc(self):
        dt = parse_iso_datetime("2026-01-19T22:50:00+00:00")
        assert dt.tzinfo is not None

    def test_valid_iso_string_naive(self):
        dt = parse_iso_datetime("2026-01-19T22:50:00")
        assert dt.year == 2026
        assert dt.tzinfo is None

    def test_invalid_string_raises_value_error(self):
        with pytest.raises(ValueError):
            parse_iso_datetime("not-a-datetime")

    def test_empty_string_raises_value_error(self):
        with pytest.raises(ValueError):
            parse_iso_datetime("")


class TestIsExpired:
    """Tests for is_expired() — uses injectable current_time parameter"""

    def test_past_datetime_is_expired(self):
        past = datetime(2020, 1, 1, tzinfo=ZoneInfo("UTC"))
        now = datetime(2026, 1, 19, tzinfo=ZoneInfo("UTC"))
        assert is_expired(past, current_time=now) is True

    def test_future_datetime_is_not_expired(self):
        future = datetime(2030, 1, 1, tzinfo=ZoneInfo("UTC"))
        now = datetime(2026, 1, 19, tzinfo=ZoneInfo("UTC"))
        assert is_expired(future, current_time=now) is False

    def test_exact_boundary_is_expired(self):
        """current_time >= expires_at → True (equal counts as expired)"""
        boundary = datetime(2026, 1, 19, 12, 0, 0, tzinfo=ZoneInfo("UTC"))
        assert is_expired(boundary, current_time=boundary) is True

    def test_one_second_before_is_not_expired(self):
        expires = datetime(2026, 1, 19, 12, 0, 0, tzinfo=ZoneInfo("UTC"))
        one_second_before = expires - timedelta(seconds=1)
        assert is_expired(expires, current_time=one_second_before) is False

    def test_injectable_current_time_overrides_real_time(self):
        """Verify that injectable current_time is actually used"""
        far_future = datetime(2099, 12, 31, tzinfo=ZoneInfo("UTC"))
        # Without injection, far_future would not be expired
        # But with a fabricated "now" even further in the future, it is
        even_further = datetime(2100, 1, 1, tzinfo=ZoneInfo("UTC"))
        assert is_expired(far_future, current_time=even_further) is True
