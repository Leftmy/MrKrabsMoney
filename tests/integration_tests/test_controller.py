import uuid
from unittest.mock import patch, MagicMock

import pytest
from app.models.payment import PaymentStatus
from app.services.payment_service import PaymentServiceError


@pytest.fixture
def sample_payment_data():
    """Fixture providing mock payment domain entity data."""
    fake_id = uuid.uuid4()
    return MagicMock(
        id=fake_id,
        stripe_intent_id="pi_test_123456789",
        amount_in_cents=1515,
        currency="usd",
        status=PaymentStatus.SUCCEEDED.value
    )


class TestCreatePaymentEndpoint:
    """Integration tests for POST /api/v1/payments endpoint."""

    def test_create_payment_success(self, client, sample_payment_data):
        """Test successful payment creation returns HTTP 201 and valid JSON structure."""
        payload = {
            "amount": 15.15,
            "currency": "USD"
        }

        with patch("app.api.v1.payment_controller.get_payment_service") as mock_get_service:
            mock_service = MagicMock()
            mock_service.create_payment.return_value = sample_payment_data
            mock_get_service.return_value = mock_service

            response = client.post("/api/v1/payments", json=payload)

        assert response.status_code == 201
        data = response.get_json()
        assert data["id"] == str(sample_payment_data.id)
        assert data["stripe_intent_id"] == "pi_test_123456789"
        assert data["amount_in_cents"] == 1515
        assert data["currency"] == "usd"
        assert data["status"] == PaymentStatus.SUCCEEDED.value

        mock_service.create_payment.assert_called_once_with(
            amount=15.15,
            currency="usd"  # Verify normalized currency
        )

    def test_create_payment_validation_error_missing_fields(self, client):
        """Test validation failure when required fields are missing returns HTTP 400."""
        payload = {
            "amount": 15.15
            # Missing currency
        }

        response = client.post("/api/v1/payments", json=payload)

        assert response.status_code == 400
        data = response.get_json()
        assert "errors" in data
        assert len(data["errors"]) > 0

    def test_create_payment_validation_error_invalid_amount(self, client):
        """Test validation failure when amount is negative or zero returns HTTP 400."""
        payload = {
            "amount": -5.00,
            "currency": "usd"
        }

        response = client.post("/api/v1/payments", json=payload)

        assert response.status_code == 400
        data = response.get_json()
        assert "errors" in data

    def test_create_payment_invalid_currency_code(self, client):
        """Test validation failure when currency code length is not 3 characters."""
        payload = {
            "amount": 10.00,
            "currency": "USDT"
        }

        response = client.post("/api/v1/payments", json=payload)

        assert response.status_code == 400
        data = response.get_json()
        assert "errors" in data

    def test_create_payment_value_error_from_service(self, client):
        """Test service ValueError handling returns HTTP 400."""
        payload = {
            "amount": 0.001,
            "currency": "usd"
        }

        with patch("app.api.v1.payment_controller.get_payment_service") as mock_get_service:
            mock_service = MagicMock()
            mock_service.create_payment.side_effect = ValueError("Invalid precision for USD currency.")
            mock_get_service.return_value = mock_service

            response = client.post("/api/v1/payments", json=payload)

        assert response.status_code == 400
        data = response.get_json()
        assert data["error"] == "Invalid precision for USD currency."

    def test_create_payment_stripe_error_returns_402(self, client):
        """Test payment failure due to Stripe card error returns HTTP 402 Payment Required."""
        payload = {
            "amount": 50.00,
            "currency": "usd"
        }

        with patch("app.api.v1.payment_controller.get_payment_service") as mock_get_service:
            mock_service = MagicMock()
            mock_service.create_payment.side_effect = PaymentServiceError("Your card was declined.")
            mock_get_service.return_value = mock_service

            response = client.post("/api/v1/payments", json=payload)

        assert response.status_code == 402
        data = response.get_json()
        assert data["error"] == "Your card was declined."


class TestGetPaymentEndpoint:
    """Integration tests for GET /api/v1/payments/<payment_id> endpoint."""

    def test_get_payment_success(self, client, sample_payment_data):
        """Test successful retrieval of payment details by ID returns HTTP 200."""
        payment_id = sample_payment_data.id

        with patch("app.api.v1.payment_controller.get_payment_service") as mock_get_service:
            mock_service = MagicMock()
            mock_service.get_payment_by_id.return_value = sample_payment_data
            mock_get_service.return_value = mock_service

            response = client.get(f"/api/v1/payments/{payment_id}")

        assert response.status_code == 200
        data = response.get_json()
        assert data["id"] == str(payment_id)
        assert data["stripe_intent_id"] == "pi_test_123456789"
        assert data["amount_in_cents"] == 1515

        mock_service.get_payment_by_id.assert_called_once_with(payment_id)

    def test_get_payment_not_found(self, client):
        """Test fetching a non-existent payment returns HTTP 404."""
        random_uuid = uuid.uuid4()

        with patch("app.api.v1.payment_controller.get_payment_service") as mock_get_service:
            mock_service = MagicMock()
            mock_service.get_payment_by_id.return_value = None
            mock_get_service.return_value = mock_service

            response = client.get(f"/api/v1/payments/{random_uuid}")

        assert response.status_code == 404
        data = response.get_json()
        assert data["error"] == "Payment not found"

    def test_get_payment_invalid_uuid_format(self, client):
        """Test providing an invalid UUID in URL path returns HTTP 404."""
        response = client.get("/api/v1/payments/not-a-valid-uuid")

        assert response.status_code == 404