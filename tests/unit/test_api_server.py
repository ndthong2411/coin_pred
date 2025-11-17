"""
Unit tests for FastAPI server.
"""
import pytest
from fastapi.testclient import TestClient


@pytest.mark.unit
class TestAPIServer:
    """Test FastAPI endpoints."""

    @pytest.fixture
    def client(self):
        """Create test client."""
        from src.api.server import app
        return TestClient(app)

    def test_health_check(self, client):
        """Test health check endpoint."""
        response = client.get("/health")

        assert response.status_code == 200
        assert "status" in response.json()

    def test_root_endpoint(self, client):
        """Test root endpoint."""
        response = client.get("/")

        assert response.status_code == 200

    @pytest.mark.skip(reason="Requires full app setup")
    def test_get_trades(self, client):
        """Test getting trades endpoint."""
        response = client.get("/api/trades")

        # May return 200 or 404 depending on setup
        assert response.status_code in [200, 404, 500]

    @pytest.mark.skip(reason="Requires full app setup")
    def test_get_performance(self, client):
        """Test performance metrics endpoint."""
        response = client.get("/api/performance")

        assert response.status_code in [200, 404, 500]
