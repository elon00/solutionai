import pytest
from httpx import AsyncClient
from sqlalchemy.orm import Session
import json
from unittest.mock import patch, MagicMock

from app.main import app
from app.database import get_db
from app.models import Ticket, ApiKey
from app.config import settings


@pytest.fixture
def test_db():
    """Create test database session"""
    # This would be replaced with a proper test database setup
    pass


@pytest.fixture
async def client(test_db):
    """Create test client"""
    async with AsyncClient(app=app, base_url="http://testserver") as client:
        yield client


class TestTicketAPI:
    """Test cases for ticket API endpoints"""

    @pytest.mark.asyncio
    async def test_triage_ticket_success(self, client):
        """Test successful ticket triage"""
        ticket_data = {
            "ticket_text": "I was charged twice this month for my premium subscription. Please refund the duplicate payment."
        }

        headers = {"X-Api-Key": "demo_key_123"}

        # Mock AI service response
        with patch('app.services.ai_service.ai_service.classify_ticket') as mock_classify:
            mock_classify.return_value = {
                "label": "billing_issue",
                "confidence": 0.95,
                "summary": "Customer reporting duplicate charges",
                "processing_time": 0.5,
                "provider": "openai"
            }

            response = await client.post("/api/v1/triage", json=ticket_data, headers=headers)

            assert response.status_code == 200
            data = response.json()
            assert data["label"] == "billing_issue"
            assert data["confidence"] == 0.95
            assert "summary" in data

    @pytest.mark.asyncio
    async def test_triage_ticket_invalid_api_key(self, client):
        """Test triage with invalid API key"""
        ticket_data = {"ticket_text": "Test ticket"}
        headers = {"X-Api-Key": "invalid_key"}

        response = await client.post("/api/v1/triage", json=ticket_data, headers=headers)

        assert response.status_code == 401
        assert "Invalid API key" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_triage_ticket_missing_api_key(self, client):
        """Test triage without API key"""
        ticket_data = {"ticket_text": "Test ticket"}

        response = await client.post("/api/v1/triage", json=ticket_data)

        assert response.status_code == 401
        assert "API key required" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_triage_ticket_rate_limit_exceeded(self, client):
        """Test rate limit exceeded"""
        ticket_data = {"ticket_text": "Test ticket"}
        headers = {"X-Api-Key": "demo_key_123"}

        # Mock rate limit exceeded
        with patch('app.services.ticket_service.TicketService._check_rate_limit') as mock_check:
            mock_check.side_effect = ValueError("Rate limit exceeded")

            response = await client.post("/api/v1/triage", json=ticket_data, headers=headers)

            assert response.status_code == 429
            assert "Rate limit exceeded" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_get_recent_tickets(self, client):
        """Test getting recent tickets"""
        headers = {"X-Api-Key": "demo_key_123"}

        response = await client.get("/api/v1/recent", headers=headers)

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

    @pytest.mark.asyncio
    async def test_get_ticket_stats(self, client):
        """Test getting ticket statistics"""
        headers = {"X-Api-Key": "demo_key_123"}

        response = await client.get("/api/v1/stats", headers=headers)

        assert response.status_code == 200
        data = response.json()
        assert "total_tickets" in data
        assert "avg_confidence" in data
        assert "label_distribution" in data


class TestHealthAPI:
    """Test cases for health check endpoints"""

    @pytest.mark.asyncio
    async def test_health_check(self, client):
        """Test basic health check"""
        response = await client.get("/health/")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] in ["healthy", "unhealthy"]
        assert "version" in data
        assert "uptime" in data

    @pytest.mark.asyncio
    async def test_detailed_health_check(self, client):
        """Test detailed health check"""
        response = await client.get("/health/detailed")

        assert response.status_code == 200
        data = response.json()
        assert "memory_usage" in data
        assert "cpu_usage" in data
        assert "timestamp" in data

    @pytest.mark.asyncio
    async def test_ping(self, client):
        """Test ping endpoint"""
        response = await client.get("/health/ping")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "pong"
        assert "timestamp" in data


class TestWebhookAPI:
    """Test cases for webhook endpoints"""

    @pytest.mark.asyncio
    async def test_stripe_webhook_success(self, client):
        """Test successful Stripe webhook processing"""
        webhook_data = {
            "type": "checkout.session.completed",
            "data": {
                "object": {
                    "customer": "cus_test123"
                }
            }
        }

        # Mock Stripe webhook signature verification
        with patch('stripe.Webhook.construct_event') as mock_construct:
            mock_construct.return_value = webhook_data

            response = await client.post("/webhook/stripe", json=webhook_data)

            assert response.status_code == 200
            assert response.json()["status"] == "success"

    @pytest.mark.asyncio
    async def test_integration_webhook(self, client):
        """Test integration webhook processing"""
        webhook_data = {
            "ticket_text": "Customer issue with login",
            "source": "zendesk"
        }

        response = await client.post("/webhook/zendesk", json=webhook_data)

        assert response.status_code == 200
        assert response.json()["status"] == "processed"


class TestAdminAPI:
    """Test cases for admin endpoints"""

    @pytest.mark.asyncio
    async def test_admin_endpoints_require_auth(self, client):
        """Test that admin endpoints require authentication"""
        endpoints = [
            "/admin/tickets",
            "/admin/api-keys",
            "/admin/webhook-logs",
            "/admin/stats"
        ]

        for endpoint in endpoints:
            response = await client.get(endpoint)
            assert response.status_code == 403

    @pytest.mark.asyncio
    async def test_admin_stats_with_auth(self, client):
        """Test admin stats with proper authentication"""
        headers = {"X-Admin-Key": settings.secret_key}

        response = await client.get("/admin/stats", headers=headers)

        assert response.status_code == 200
        data = response.json()
        assert "tickets" in data
        assert "api_keys" in data
        assert "performance" in data


class TestErrorHandling:
    """Test error handling scenarios"""

    @pytest.mark.asyncio
    async def test_invalid_json_payload(self, client):
        """Test handling of invalid JSON payload"""
        headers = {"X-Api-Key": "demo_key_123"}

        response = await client.post(
            "/api/v1/triage",
            content="invalid json",
            headers=headers
        )

        assert response.status_code == 422  # Validation error

    @pytest.mark.asyncio
    async def test_empty_ticket_text(self, client):
        """Test handling of empty ticket text"""
        ticket_data = {"ticket_text": ""}
        headers = {"X-Api-Key": "demo_key_123"}

        response = await client.post("/api/v1/triage", json=ticket_data, headers=headers)

        assert response.status_code == 422  # Validation error

    @pytest.mark.asyncio
    async def test_oversized_ticket_text(self, client):
        """Test handling of oversized ticket text"""
        ticket_data = {"ticket_text": "x" * 10001}  # Over 10k limit
        headers = {"X-Api-Key": "demo_key_123"}

        response = await client.post("/api/v1/triage", json=ticket_data, headers=headers)

        assert response.status_code == 422  # Validation error


# Integration tests
class TestIntegration:
    """Integration test cases"""

    @pytest.mark.asyncio
    async def test_full_ticket_workflow(self, client):
        """Test complete ticket processing workflow"""
        ticket_data = {
            "ticket_text": "I cannot access my account after password reset"
        }
        headers = {"X-Api-Key": "demo_key_123"}

        # Submit ticket
        response = await client.post("/api/v1/triage", json=ticket_data, headers=headers)
        assert response.status_code == 200

        # Get recent tickets
        response = await client.get("/api/v1/recent", headers=headers)
        assert response.status_code == 200
        assert len(response.json()) > 0

        # Get stats
        response = await client.get("/api/v1/stats", headers=headers)
        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_concurrent_requests(self, client):
        """Test handling of concurrent requests"""
        import asyncio

        ticket_data = {"ticket_text": "Concurrent test ticket"}
        headers = {"X-Api-Key": "demo_key_123"}

        # Send multiple concurrent requests
        tasks = []
        for i in range(5):
            task = client.post("/api/v1/triage", json=ticket_data, headers=headers)
            tasks.append(task)

        responses = await asyncio.gather(*tasks)

        # All should succeed (within rate limits)
        success_count = sum(1 for r in responses if r.status_code == 200)
        rate_limit_count = sum(1 for r in responses if r.status_code == 429)

        assert success_count + rate_limit_count == 5