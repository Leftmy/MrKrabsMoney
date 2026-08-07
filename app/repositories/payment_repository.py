from typing import Optional
from app.extensions import db
from app.models.payment import Payment, PaymentStatus


class PaymentRepository:
    """Repository for handling database operations for the Payment model."""

    def create(
        self,
        stripe_intent_id: str,
        amount_in_cents: int,
        currency: str = "usd",
        status: str = PaymentStatus.PENDING.value
    ) -> Payment:
        """Create and persist a new payment record in the database."""
        payment = Payment(
            stripe_intent_id=stripe_intent_id,
            amount_in_cents=amount_in_cents,
            currency=currency.lower(),
            status=status
        )
        db.session.add(payment)
        db.session.commit()
        return payment

    def get_by_stripe_id(self, stripe_intent_id: str) -> Optional[Payment]:
        """Retrieve a payment record by its Stripe Intent ID."""
        return Payment.query.filter_by(stripe_intent_id=stripe_intent_id).first()

    def get_by_id(self, payment_id: int) -> Optional[Payment]:
        """Retrieve a payment record by its primary key ID."""
        return Payment.query.get(payment_id)

    def update_status(self, stripe_intent_id: str, status: str) -> Optional[Payment]:
        """
        Update the status of a payment matching the given stripe_intent_id.
        Returns the updated Payment object, or None if not found.
        """
        payment = self.get_by_stripe_id(stripe_intent_id)
        if not payment:
            return None

        payment.status = status
        db.session.commit()
        return payment