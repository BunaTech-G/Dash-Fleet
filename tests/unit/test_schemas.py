"""
Unit tests for schemas module (Marshmallow validation).

Tests API request/response validation.
"""

import pytest
from marshmallow import ValidationError
from schemas import ReportSchema, MetricsSchema


class TestReportSchema:
    """Tests for ReportSchema validation."""

    def test_valid_report(self):
        """Test validation of a valid report."""
        schema = ReportSchema()
        data = {
            "machine_id": "test-machine",
            "report": {
                "cpu_percent": 35.5,
                "ram_percent": 62.1,
                "disk_percent": 45.3,
                "uptime": 86400,
                "timestamp": 1704067200.0
            }
        }
        result = schema.load(data)
        assert result["machine_id"] == "test-machine"
        assert result["report"]["cpu_percent"] == 35.5

    def test_missing_machine_id(self):
        """Test validation fails when machine_id is missing."""
        schema = ReportSchema()
        data = {
            "report": {
                "cpu_percent": 35.5,
                "ram_percent": 62.1,
                "disk_percent": 45.3
            }
        }
        with pytest.raises(ValidationError) as exc_info:
            schema.load(data)
        assert "machine_id" in exc_info.value.messages

    def test_missing_report(self):
        """Test validation fails when report is missing."""
        schema = ReportSchema()
        data = {
            "machine_id": "test-machine"
        }
        with pytest.raises(ValidationError) as exc_info:
            schema.load(data)
        assert "report" in exc_info.value.messages

    def test_machine_id_not_string(self):
        """Test validation fails when machine_id is not a string."""
        schema = ReportSchema()
        data = {
            "machine_id": 12345,
            "report": {"cpu_percent": 35.5}
        }
        with pytest.raises(ValidationError) as exc_info:
            schema.load(data)
        assert "machine_id" in exc_info.value.messages

    def test_report_not_dict(self):
        """Test validation fails when report is not a dict."""
        schema = ReportSchema()
        data = {
            "machine_id": "test-machine",
            "report": "not a dict"
        }
        with pytest.raises(ValidationError) as exc_info:
            schema.load(data)
        assert "report" in exc_info.value.messages


class TestMetricsSchema:
    """Tests for MetricsSchema validation."""

    def test_valid_metrics(self):
        """Test validation of valid metrics."""
        schema = MetricsSchema()
        data = {
            "cpu_percent": 35.5,
            "ram_percent": 62.1,
            "disk_percent": 45.3,
            "uptime": 86400,
            "timestamp": 1704067200.0
        }
        result = schema.load(data)
        assert result["cpu_percent"] == 35.5
        assert result["ram_percent"] == 62.1
        assert result["disk_percent"] == 45.3

    def test_valid_metrics_minimal(self):
        """Test validation of metrics with only required fields."""
        schema = MetricsSchema()
        data = {
            "cpu_percent": 35.5,
            "ram_percent": 62.1,
            "disk_percent": 45.3
        }
        result = schema.load(data)
        assert result["cpu_percent"] == 35.5

    def test_missing_cpu_percent(self):
        """Test validation fails when cpu_percent is missing."""
        schema = MetricsSchema()
        data = {
            "ram_percent": 62.1,
            "disk_percent": 45.3
        }
        with pytest.raises(ValidationError) as exc_info:
            schema.load(data)
        assert "cpu_percent" in exc_info.value.messages

    def test_cpu_percent_out_of_range(self):
        """Test validation fails when cpu_percent is out of range."""
        schema = MetricsSchema()
        data = {
            "cpu_percent": 150.0,  # Invalid: > 100
            "ram_percent": 62.1,
            "disk_percent": 45.3
        }
        with pytest.raises(ValidationError) as exc_info:
            schema.load(data)
        assert "cpu_percent" in exc_info.value.messages

    def test_negative_percentages(self):
        """Test validation fails with negative percentages."""
        schema = MetricsSchema()
        data = {
            "cpu_percent": -5.0,
            "ram_percent": 62.1,
            "disk_percent": 45.3
        }
        with pytest.raises(ValidationError) as exc_info:
            schema.load(data)
        assert "cpu_percent" in exc_info.value.messages

    def test_ram_percent_bounds(self):
        """Test ram_percent validation."""
        schema = MetricsSchema()
        # Valid
        result = schema.load({
            "cpu_percent": 35.5,
            "ram_percent": 100.0,
            "disk_percent": 45.3
        })
        assert result["ram_percent"] == 100.0

        # Invalid
        with pytest.raises(ValidationError):
            schema.load({
                "cpu_percent": 35.5,
                "ram_percent": 120.0,
                "disk_percent": 45.3
            })

    def test_disk_percent_bounds(self):
        """Test disk_percent validation."""
        schema = MetricsSchema()
        # Valid
        result = schema.load({
            "cpu_percent": 35.5,
            "ram_percent": 62.1,
            "disk_percent": 0.0
        })
        assert result["disk_percent"] == 0.0

        # Invalid
        with pytest.raises(ValidationError):
            schema.load({
                "cpu_percent": 35.5,
                "ram_percent": 62.1,
                "disk_percent": -10.0
            })
