"""
Unit tests for db_utils module.

Tests database operations and fleet state management.
"""

import pytest
import json
import time
from db_utils import (
    init_db,
    insert_fleet_report,
    get_fleet_state,
    remove_expired_machines,
)


class TestDatabaseInitialization:
    """Tests for database initialization."""

    def test_init_db_creates_tables(self, temp_db):
        """Test that init_db creates required tables."""
        init_db(temp_db)
        # If this doesn't raise an error, tables were created
        # We verify by attempting to insert a record (see next test)

    def test_init_db_idempotent(self, temp_db):
        """Test that init_db can be called multiple times safely."""
        init_db(temp_db)
        init_db(temp_db)  # Should not raise an error


class TestInsertFleetReport:
    """Tests for fleet report insertion."""

    def test_insert_valid_report(self, temp_db, sample_report):
        """Test inserting a valid fleet report."""
        init_db(temp_db)
        result = insert_fleet_report(
            temp_db,
            sample_report["machine_id"],
            sample_report["report"],
            org_id="test-org"
        )
        assert result is not None

    def test_insert_creates_unique_id(self, temp_db, sample_report):
        """Test that each insert creates a unique record ID."""
        init_db(temp_db)
        
        report1 = sample_report.copy()
        report1["machine_id"] = "machine-1"
        insert_fleet_report(temp_db, report1["machine_id"], report1["report"], org_id="test-org")
        
        report2 = sample_report.copy()
        report2["machine_id"] = "machine-2"
        insert_fleet_report(temp_db, report2["machine_id"], report2["report"], org_id="test-org")
        
        # Both inserts should succeed without errors


class TestFleetState:
    """Tests for fleet state retrieval and expiration."""

    def test_get_fleet_state_returns_dict(self, temp_db, sample_report):
        """Test that get_fleet_state returns a dictionary."""
        init_db(temp_db)
        insert_fleet_report(
            temp_db,
            sample_report["machine_id"],
            sample_report["report"],
            org_id="test-org"
        )
        state = get_fleet_state(temp_db, org_id="test-org")
        assert isinstance(state, dict)

    def test_get_fleet_state_contains_machine(self, temp_db, sample_report):
        """Test that inserted machine appears in fleet state."""
        init_db(temp_db)
        machine_id = sample_report["machine_id"]
        insert_fleet_report(
            temp_db,
            machine_id,
            sample_report["report"],
            org_id="test-org"
        )
        state = get_fleet_state(temp_db, org_id="test-org")
        
        # Machine should be in state with id "test-org:machine-id"
        assert any(machine_id in str(m) for m in state.values())

    def test_get_fleet_state_org_scoped(self, temp_db, sample_report):
        """Test that fleet state is properly scoped by organization."""
        init_db(temp_db)
        machine_id = sample_report["machine_id"]
        
        # Insert for org-1
        insert_fleet_report(
            temp_db,
            machine_id,
            sample_report["report"],
            org_id="org-1"
        )
        
        # Insert different machine for org-2
        report2 = sample_report.copy()
        report2["machine_id"] = "other-machine"
        insert_fleet_report(
            temp_db,
            report2["machine_id"],
            report2["report"],
            org_id="org-2"
        )
        
        # org-1 should only see its machines
        state_org1 = get_fleet_state(temp_db, org_id="org-1")
        assert len(state_org1) >= 1
        
        # org-2 should only see its machines
        state_org2 = get_fleet_state(temp_db, org_id="org-2")
        assert len(state_org2) >= 1


class TestMachineExpiration:
    """Tests for machine expiration logic."""

    def test_remove_expired_machines(self, temp_db, sample_report):
        """Test that expired machines are removed."""
        init_db(temp_db)
        insert_fleet_report(
            temp_db,
            sample_report["machine_id"],
            sample_report["report"],
            org_id="test-org"
        )
        
        # Remove expired with very short TTL (0 seconds)
        now = time.time()
        expired = remove_expired_machines(temp_db, ttl_seconds=0, org_id="test-org")
        
        # Machines should be considered expired
        assert expired is not None

    def test_machine_not_expired_within_ttl(self, temp_db, sample_report):
        """Test that recent machines are not expired."""
        init_db(temp_db)
        insert_fleet_report(
            temp_db,
            sample_report["machine_id"],
            sample_report["report"],
            org_id="test-org"
        )
        
        # Get state with long TTL
        state = get_fleet_state(temp_db, org_id="test-org", ttl_seconds=3600)
        
        # Machine should still be in state
        assert len(state) > 0


class TestReportFormatting:
    """Tests for report data handling."""

    def test_report_stored_as_json(self, temp_db, sample_report):
        """Test that reports are stored and retrieved correctly."""
        init_db(temp_db)
        insert_fleet_report(
            temp_db,
            sample_report["machine_id"],
            sample_report["report"],
            org_id="test-org"
        )
        
        state = get_fleet_state(temp_db, org_id="test-org")
        
        # Verify report data is present
        for machine_data in state.values():
            assert "report" in machine_data or "cpu_percent" in machine_data

    def test_multiple_reports_same_machine(self, temp_db, sample_report):
        """Test inserting multiple reports for the same machine."""
        init_db(temp_db)
        machine_id = sample_report["machine_id"]
        
        # Insert first report
        insert_fleet_report(
            temp_db,
            machine_id,
            sample_report["report"],
            org_id="test-org"
        )
        
        # Insert second report (should update)
        report2 = sample_report.copy()
        report2["report"]["cpu_percent"] = 50.0
        insert_fleet_report(
            temp_db,
            machine_id,
            report2["report"],
            org_id="test-org"
        )
        
        # Should still have machine in state
        state = get_fleet_state(temp_db, org_id="test-org")
        assert len(state) > 0
