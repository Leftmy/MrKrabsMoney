from unittest.mock import MagicMock, patch
import pytest
from app.models.payment import Payment, PaymentStatus
from app.repositories.payment_repository import PaymentRepository


@pytest.fixture
def repo():
    return PaymentRepository()


def test_create_payment(repo):
    # Arrange
    mock_session = MagicMock()
    with patch("app.repositories.payment_repository.db.session", mock_session):
        stripe_id = "pi_test_123"
        amount_in_cents = 1515
        currency = "usd"
        status = PaymentStatus.PENDING.value

        # Act
        payment = repo.create(
            stripe_intent_id=stripe_id,
            amount_in_cents=amount_in_cents,
            currency=currency,
            status=status
        )

        # Assert
        mock_session.add.assert_called_once()
        mock_session.commit.assert_called_once()
        assert payment.stripe_intent_id == stripe_id
        assert payment.amount_in_cents == amount_in_cents
        assert payment.status == status


def test_update_status_success(repo):
    # Arrange
    stripe_id = "pi_test_123"
    mock_payment = Payment(stripe_intent_id=stripe_id, status=PaymentStatus.PENDING.value)

    mock_query = MagicMock()
    mock_query.filter_by.return_value.first.return_value = mock_payment

    mock_session = MagicMock()
    with patch("app.repositories.payment_repository.db.session", mock_session), \
         patch("app.models.payment.Payment.query", mock_query):

        # Act
        updated_payment = repo.update_status(stripe_id, PaymentStatus.SUCCEEDED.value)

        # Assert
        assert updated_payment is not None
        assert updated_payment.status == PaymentStatus.SUCCEEDED.value
        mock_session.commit.assert_called_once()


def test_update_status_not_found(repo):
    # Arrange
    mock_query = MagicMock()
    mock_query.filter_by.return_value.first.return_value = None

    with patch("app.models.payment.Payment.query", mock_query):
        # Act
        updated_payment = repo.update_status("non_existent_id", PaymentStatus.SUCCEEDED.value)

        # Assert
        assert updated_payment is None