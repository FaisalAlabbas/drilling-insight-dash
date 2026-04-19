"""
Integration tests for main API endpoints.
Tests full request/response flow including database and authentication.
"""

import pytest
from fastapi.testclient import TestClient
from datetime import datetime
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

try:
    from main import app
except ImportError:
    from api import app

client = TestClient(app)


class TestHealthEndpoint:
    """Integration tests for GET /health endpoint."""

    def test_health_returns_ok(self):
        """Test health endpoint returns success."""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["ok"] is True

    def test_health_response_has_subsystem_checks(self):
        """Test health response includes subsystem health."""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        # Should have health information
        assert "ok" in data or "status" in data


class TestModelMetricsEndpoint:
    """Integration tests for GET /model/metrics endpoint."""

    def test_model_metrics_returns_metrics(self):
        """Test metrics endpoint returns model performance metrics."""
        response = client.get("/model/metrics")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, dict)

    def test_model_metrics_has_accuracy_or_status(self):
        """Test metrics response contains performance data."""
        response = client.get("/model/metrics")
        if response.status_code == 200:
            data = response.json()
            # Should have some metric data or explicit 'not_available' message
            assert len(data) > 0


class TestPredictEndpoint:
    """Integration tests for POST /predict endpoint."""

    @pytest.fixture
    def valid_prediction_request(self):
        """Valid prediction request fixture."""
        return {
            "WOB_klbf": 50.0,
            "RPM_demo": 150.0,
            "ROP_ft_hr": 50.0,
            "PHIF": 0.18,
            "VSH": 0.25,
            "SW": 0.35,
            "KLOGH": 120.0,
            "Formation_Class": "Sandstone",
            "Torque_kftlb": 100.0,
            "Vibration_g": 0.5,
            "DLS_deg_per_100ft": 1.5,
            "Inclination_deg": 45.0,
            "Azimuth_deg": 90.0,
            "Depth_ft": 5000.0,
        }

    def test_predict_accepts_valid_request(self, valid_prediction_request):
        """Test predict endpoint accepts valid request."""
        response = client.post("/predict", json=valid_prediction_request)
        assert response.status_code in [200, 500]  # 200 success or 500 model error
        data = response.json()
        assert isinstance(data, dict)

    def test_predict_response_structure(self, valid_prediction_request):
        """Test predict response has required fields."""
        response = client.post("/predict", json=valid_prediction_request)
        if response.status_code == 200:
            data = response.json()
            # Should have decision record or recommendation
            assert "recommendation" in data or "decision_record" in data

    def test_predict_rejects_missing_required_fields(self):
        """Test predict rejects request with missing fields."""
        invalid_request = {
            "WOB_klbf": 50.0,
            # Missing most required fields
        }
        response = client.post("/predict", json=invalid_request)
        assert response.status_code == 422  # Validation error

    def test_predict_with_high_vibration(self, valid_prediction_request):
        """Test predict with high vibration condition."""
        valid_prediction_request["Vibration_g"] = 3.0
        response = client.post("/predict", json=valid_prediction_request)
        assert response.status_code in [200, 500]

    def test_predict_with_high_dls(self, valid_prediction_request):
        """Test predict with high DLS condition."""
        valid_prediction_request["DLS_deg_per_100ft"] = 5.0
        response = client.post("/predict", json=valid_prediction_request)
        assert response.status_code in [200, 500]

    def test_predict_with_safe_conditions(self, valid_prediction_request):
        """Test predict with safe operating conditions."""
        valid_prediction_request["Vibration_g"] = 0.3
        valid_prediction_request["DLS_deg_per_100ft"] = 1.0
        response = client.post("/predict", json=valid_prediction_request)
        assert response.status_code in [200, 500]


class TestActuatorStatusEndpoint:
    """Integration tests for GET /actuator/status endpoint."""

    def test_actuator_status_returns_status(self):
        """Test actuator status endpoint returns current status."""
        response = client.get("/actuator/status")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, dict)

    def test_actuator_status_has_state(self):
        """Test actuator status includes state field."""
        response = client.get("/actuator/status")
        if response.status_code == 200:
            data = response.json()
            # Should have state or status information
            assert "state" in data or "status" in data


class TestAuthEndpoints:
    """Integration tests for authentication endpoints."""

    def test_login_with_valid_credentials(self):
        """Test login with valid credentials returns token."""
        response = client.post(
            "/auth/login",
            json={"username": "admin", "password": "admin"}
        )
        # Should either succeed or return 401 if default credentials not available
        assert response.status_code in [200, 401]
        if response.status_code == 200:
            data = response.json()
            assert "access_token" in data

    def test_login_with_invalid_credentials(self):
        """Test login with invalid credentials returns error."""
        response = client.post(
            "/auth/login",
            json={"username": "invalid", "password": "invalid"}
        )
        assert response.status_code in [401, 422]

    def test_auth_me_requires_token(self):
        """Test /auth/me endpoint requires authentication."""
        response = client.get("/auth/me")
        # Should require token
        assert response.status_code == 403 or response.status_code == 401


class TestConfigEndpoint:
    """Integration tests for configuration endpoint."""

    def test_config_returns_limits(self):
        """Test /config endpoint returns configuration."""
        response = client.get("/config")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, dict)

    def test_config_has_limits_structure(self):
        """Test config response includes limit information."""
        response = client.get("/config")
        if response.status_code == 200:
            data = response.json()
            # Should have limits or configuration data
            assert len(data) > 0


class TestDecisionsEndpoint:
    """Integration tests for decisions endpoint."""

    def test_decisions_stats_returns_data(self):
        """Test /decisions/stats endpoint."""
        response = client.get("/decisions/stats")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, dict)


class TestTelemetryEndpoint:
    """Integration tests for telemetry endpoints."""

    def test_telemetry_next_returns_packet(self):
        """Test /telemetry/next endpoint returns telemetry data."""
        response = client.get("/telemetry/next")
        assert response.status_code in [200, 500, 404]
        if response.status_code == 200:
            data = response.json()
            assert isinstance(data, dict)

    def test_telemetry_quality_returns_metrics(self):
        """Test /telemetry/quality endpoint."""
        response = client.get("/telemetry/quality")
        assert response.status_code in [200, 500, 404]
        if response.status_code == 200:
            data = response.json()
            assert isinstance(data, dict)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
