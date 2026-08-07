import uuid
from unittest.mock import MagicMock, patch
import pytest
import stripe

from app.models.payment import PaymentStatus
from app.services.payment_service import PaymentService, PaymentServiceError


# --- Tests for create_payment ---

def test_create_payment_success_usd(app, mock_stripe_payment_intent):
    """Test successful payment creation for standard currency (USD)."""
    mock_repo = MagicMock()
    fake_uuid = uuid.uuid4()
    fake_payment = MagicMock(
        id=fake_uuid,
        stripe_intent_id="pi_test_123456789",
        amount_in_cents=1515,
        currency="usd",
        status=PaymentStatus.SUCCEEDED.value
    )
    mock_repo.create.return_value = fake_payment

    service = PaymentService(repository=mock_repo)
    result = service.create_payment(amount=15.15, currency="usd")

    mock_stripe_payment_intent.assert_called_once_with(
        amount=1515,
        currency="usd",
        payment_method="pm_card_visa",
        confirm=True,
        automatic_payment_methods={"enabled": True, "allow_redirects": "never"}
    )
    mock_repo.create.assert_called_once_with(
        stripe_intent_id="pi_test_123456789",
        amount_in_cents=1515,
        currency="usd",
        status=PaymentStatus.SUCCEEDED.value
    )
    assert result == fake_payment


def test_create_payment_zero_decimal_currency(app, mock_stripe_payment_intent):
    """Test payment creation for zero-decimal currency (JPY)."""
    mock_repo = MagicMock()
    service = PaymentService(repository=mock_repo)

    service.create_payment(amount=500, currency="jpy")

    mock_stripe_payment_intent.assert_called_once_with(
        amount=500,
        currency="jpy",
        payment_method="pm_card_visa",
        confirm=True,
        automatic_payment_methods={"enabled": True, "allow_redirects": "never"}
    )
    mock_repo.create.assert_called_once_with(
        stripe_intent_id="pi_test_123456789",
        amount_in_cents=500,
        currency="jpy",
        status=PaymentStatus.SUCCEEDED.value
    )


def test_create_payment_invalid_amount_raises_value_error(app):
    """Test that creating a payment with invalid decimal precision raises ValueError."""
    mock_repo = MagicMock()
    service = PaymentService(repository=mock_repo)

    with pytest.raises(ValueError, match="allows at most 2"):
        service.create_payment(amount=10.123, currency="usd")

    mock_repo.create.assert_not_called()


def test_create_payment_stripe_card_error(app):
    """Test that Stripe CardError is caught and re-raised as PaymentServiceError."""
    mock_repo = MagicMock()
    service = PaymentService(repository=mock_repo)

    stripe_error = stripe.error.CardError(
        message="Your card was declined.",
        param="card",
        code="card_declined"
    )

    with patch("stripe.PaymentIntent.create", side_effect=stripe_error):
        with pytest.raises(PaymentServiceError, match="Payment failed: Your card was declined."):
            service.create_payment(amount=50.00, currency="usd")

    mock_repo.create.assert_not_called()


# --- Tests for get_payment ---

def test_get_payment_by_id_success(app):
    """Test retrieving a payment by its primary key UUID."""
    mock_repo = MagicMock()
    fake_uuid = uuid.uuid4()
    fake_payment = MagicMock(id=fake_uuid)
    mock_repo.get_by_id.return_value = fake_payment

    service = PaymentService(repository=mock_repo)
    result = service.get_payment_by_id(fake_uuid)

    mock_repo.get_by_id.assert_called_once_with(fake_uuid)
    assert result == fake_payment


def test_get_payment_by_stripe_id_success(app):
    """Test retrieving a payment by Stripe Intent ID."""
    mock_repo = MagicMock()
    fake_payment = MagicMock(stripe_intent_id="pi_test_999")
    mock_repo.get_by_stripe_id.return_value = fake_payment

    service = PaymentService(repository=mock_repo)
    result = service.get_payment_by_stripe_id("pi_test_999")

    mock_repo.get_by_stripe_id.assert_called_once_with("pi_test_999")
    assert result == fake_payment


def test_get_payment_not_found_returns_none(app):
    """Test retrieving a non-existent payment returns None."""
    mock_repo = MagicMock()
    mock_repo.get_by_id.return_value = None

    service = PaymentService(repository=mock_repo)
    result = service.get_payment_by_id(uuid.uuid4())

    assert result is None


# --- Tests for update_payment_status ---

def test_update_payment_status_success(app):
    """Test updating payment status via service."""
    mock_repo = MagicMock()
    fake_payment = MagicMock(status=PaymentStatus.SUCCEEDED.value)
    mock_repo.update_status.return_value = fake_payment

    service = PaymentService(repository=mock_repo)
    result = service.update_payment_status("pi_test_100", PaymentStatus.SUCCEEDED.value)

    mock_repo.update_status.assert_called_once_with("pi_test_100", PaymentStatus.SUCCEEDED.value)
    assert result == fake_payment
