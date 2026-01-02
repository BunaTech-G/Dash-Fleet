"""
Pytest configuration and fixtures for DashFleet tests.
"""

import pytest
import tempfile
from pathlib import Path
import json


@pytest.fixture
def temp_db():
    """Create temporary SQLite database for testing."""
    with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
        db_path = f.name
    yield db_path
    Path(db_path).unlink(missing_ok=True)


@pytest.fixture
def sample_report():
    """Sample fleet metric report."""
    return {
        "cpu_percent": 45.2,
        "ram_percent": 62.1,
        "disk_percent": 78.5,
        "uptime_hms": "12:34:56",
        "uptime_seconds": 45296,
        "health": {
            "score": 75,
            "status": "warn"
        }
    }


@pytest.fixture
def sample_machine_stats():
    """Sample complete machine stats."""
    return {
        "cpu_percent": 42.0,
        "ram_percent": 65.0,
        "disk_percent": 80.0,
        "uptime_seconds": 86400,
        "uptime_hms": "24:00:00",
        "ram_used_gib": 8.2,
        "ram_total_gib": 16.0,
        "disk_used_gib": 400.0,
        "disk_total_gib": 512.0,
    }
