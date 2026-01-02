"""
Unit tests for fleet_utils module.

Tests health score calculation, formatting functions.
"""

import pytest
from fleet_utils import (
    calculate_health_score,
    format_bytes_to_gib,
    format_uptime_hms
)


class TestHealthScoreCalculation:
    """Tests for health score calculation."""

    def test_perfect_health(self):
        """Test health score when all metrics are excellent."""
        stats = {
            "cpu_percent": 10.0,
            "ram_percent": 30.0,
            "disk_percent": 40.0,
        }
        result = calculate_health_score(stats)
        assert result["score"] >= 80
        assert result["status"] == "ok"

    def test_warning_health(self):
        """Test health score in warning range."""
        stats = {
            "cpu_percent": 75.0,
            "ram_percent": 75.0,
            "disk_percent": 75.0,
        }
        result = calculate_health_score(stats)
        assert 60 <= result["score"] < 80
        assert result["status"] == "warn"

    def test_critical_health(self):
        """Test health score in critical range."""
        stats = {
            "cpu_percent": 95.0,
            "ram_percent": 90.0,
            "disk_percent": 95.0,
        }
        result = calculate_health_score(stats)
        assert result["score"] < 60
        assert result["status"] == "critical"

    def test_mixed_metrics(self):
        """Test health score with mixed metric levels."""
        stats = {
            "cpu_percent": 30.0,
            "ram_percent": 75.0,  # High RAM
            "disk_percent": 50.0,
        }
        result = calculate_health_score(stats)
        assert "score" in result
        assert "status" in result
        assert 0 <= result["score"] <= 100


class TestFormatBytesToGib:
    """Tests for byte to GiB conversion."""

    def test_zero_bytes(self):
        """Test conversion of zero bytes."""
        assert format_bytes_to_gib(0) == 0.0

    def test_one_gib(self):
        """Test conversion of one GiB."""
        # 1 GiB = 1073741824 bytes
        result = format_bytes_to_gib(1073741824)
        assert abs(result - 1.0) < 0.01

    def test_fractional_gib(self):
        """Test conversion of fractional GiB."""
        # 512 MiB = 0.5 GiB = 536870912 bytes
        result = format_bytes_to_gib(536870912)
        assert abs(result - 0.5) < 0.01

    def test_large_value(self):
        """Test conversion of large byte values."""
        # 100 GiB
        result = format_bytes_to_gib(107374182400)
        assert abs(result - 100.0) < 0.1


class TestFormatUptimeHms:
    """Tests for uptime formatting (HH:MM:SS)."""

    def test_zero_seconds(self):
        """Test formatting zero seconds."""
        assert format_uptime_hms(0) == "00:00:00"

    def test_one_minute(self):
        """Test formatting 60 seconds."""
        assert format_uptime_hms(60) == "00:01:00"

    def test_one_hour(self):
        """Test formatting 3600 seconds."""
        assert format_uptime_hms(3600) == "01:00:00"

    def test_one_day(self):
        """Test formatting 86400 seconds (1 day)."""
        assert format_uptime_hms(86400) == "24:00:00"

    def test_mixed_time(self):
        """Test formatting mixed time."""
        # 1 hour + 23 minutes + 45 seconds = 5025 seconds
        assert format_uptime_hms(5025) == "01:23:45"

    def test_large_uptime(self):
        """Test formatting large uptime (100 days)."""
        seconds = 100 * 86400 + 5 * 3600 + 30 * 60 + 45  # 100d 5h 30m 45s
        result = format_uptime_hms(seconds)
        # Should format as "X:XX:XX" where first part is hours
        assert ":" in result
