from typing import Optional
import uuid
from decimal import Decimal
import stripe
from flask import current_app

from app.models.payment import Payment
from app.repositories.payment_repository import PaymentRepository
from app.utils.currency import to_stripe_amount


class PaymentServiceError(Exception):
    """Custom exception raised when payment processing fails."""
    pass


class PaymentService:
    """Service layer handling payment processing logic and Stripe API integration."""

    def __init__(self, repository: Optional[PaymentRepository] = None) -> None:
        self.repository = repository or PaymentRepository()

    def create_payment(self, amount: float | Decimal, currency: str = "usd") -> Payment:
        """
        Create a Stripe PaymentIntent with instant test card confirmation
        and persist the payment record in the database.

        Raises:
            ValueError: If the amount has more decimal places than allowed by the currency.
            PaymentServiceError: If the Stripe API call fails.
        """
        stripe.api_key = current_app.config["STRIPE_SECRET_KEY"]

        currency_clean = currency.lower().strip()
        stripe_amount = to_stripe_amount(amount, currency_clean)

        try:
            intent = stripe.PaymentIntent.create(
                amount=stripe_amount,
                currency=currency_clean,
                payment_method="pm_card_visa",
                confirm=True,
                automatic_payment_methods={"enabled": True, "allow_redirects": "never"}
            )
        except stripe.error.StripeError as e:
            error_message = getattr(e, "user_message", None) or str(e)
            raise PaymentServiceError(f"Payment failed: {error_message}") from e

        return self.repository.create(
            stripe_intent_id=intent.id,
            amount_in_cents=stripe_amount,
            currency=currency_clean,
            status=intent.status
        )

    def get_payment_by_id(self, payment_id: str | uuid.UUID) -> Optional[Payment]:
        """Retrieve a payment record by its primary key UUID."""
        return self.repository.get_by_id(payment_id)

    def get_payment_by_stripe_id(self, stripe_intent_id: str) -> Optional[Payment]:
        """Retrieve a payment record by its Stripe Intent ID."""
        return self.repository.get_by_stripe_id(stripe_intent_id)

    def update_payment_status(self, stripe_intent_id: str, status: str) -> Optional[Payment]:
        """Update the status of a payment matching the given stripe_intent_id."""
        return self.repository.update_status(stripe_intent_id, status)