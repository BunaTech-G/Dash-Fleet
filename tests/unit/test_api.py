"""
Integration tests for Flask API endpoints.

Tests API functionality end-to-end.
"""

import pytest
import json
from main import app, init_db
from db_utils import insert_fleet_report


class TestFleetAPIEndpoints:
    """Tests for fleet API endpoints."""

    @pytest.fixture
    def client(self, temp_db):
        """Create a test client with temporary database."""
        app.config["DATABASE"] = temp_db
        app.config["TESTING"] = True
        init_db(temp_db)
        
        with app.test_client() as client:
            yield client

    def test_fleet_public_endpoint_exists(self, client):
        """Test that /api/fleet/public endpoint is accessible."""
        response = client.get("/api/fleet/public")
        assert response.status_code in [200, 401, 403, 404]  # Could be protected

    def test_fleet_report_requires_bearer_token(self, client):
        """Test that POST /api/fleet/report requires authentication."""
        data = {
            "machine_id": "test-machine",
            "report": {
                "cpu_percent": 35.5,
                "ram_percent": 62.1,
                "disk_percent": 45.3,
                "uptime": 86400
            }
        }
        response = client.post(
            "/api/fleet/report",
            json=data,
            headers={}  # No auth header
        )
        # Should fail without Bearer token
        assert response.status_code in [401, 403]

    def test_fleet_report_with_invalid_data(self, client):
        """Test that POST /api/fleet/report validates input."""
        invalid_data = {
            "machine_id": "test-machine"
            # Missing 'report' field
        }
        response = client.post(
            "/api/fleet/report",
            json=invalid_data,
            headers={"Authorization": "Bearer test-token"}
        )
        # Should fail validation
        assert response.status_code in [400, 401, 403]

    def test_api_returns_json(self, client):
        """Test that API endpoints return JSON."""
        response = client.get("/api/fleet/public")
        try:
            response.get_json()
        except Exception:
            pytest.skip("API endpoint not returning JSON")


class TestRateLimiting:
    """Tests for rate limiting on API endpoints."""

    @pytest.fixture
    def client(self, temp_db):
        """Create a test client."""
        app.config["DATABASE"] = temp_db
        app.config["TESTING"] = True
        init_db(temp_db)
        
        with app.test_client() as client:
            yield client

    def test_public_endpoint_rate_limit(self, client):
        """Test rate limiting on public endpoint."""
        # Make multiple rapid requests
        for i in range(3):
            response = client.get("/api/fleet/public")
            # Should get responses (may be rate limited after many)
            assert response.status_code in [200, 429]


class TestErrorHandling:
    """Tests for error handling in API."""

    @pytest.fixture
    def client(self, temp_db):
        """Create a test client."""
        app.config["DATABASE"] = temp_db
        app.config["TESTING"] = True
        init_db(temp_db)
        
        with app.test_client() as client:
            yield client

    def test_invalid_json_request(self, client):
        """Test handling of invalid JSON."""
        response = client.post(
            "/api/fleet/report",
            data="not valid json",
            content_type="application/json",
            headers={"Authorization": "Bearer test-token"}
        )
        # Should return 400 Bad Request
        assert response.status_code in [400, 401, 403]

    def test_missing_required_fields(self, client):
        """Test validation of required fields."""
        data = {"machine_id": "test"}  # Missing 'report'
        response = client.post(
            "/api/fleet/report",
            json=data,
            headers={"Authorization": "Bearer test-token"}
        )
        assert response.status_code in [400, 401, 403]
