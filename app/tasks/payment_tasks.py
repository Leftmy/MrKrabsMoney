import logging
from celery import shared_task

from app.repositories.payment_repository import PaymentRepository
from app.services.payment_service import PaymentService

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=3, default_retry_delay=5)
def process_stripe_webhook_task(self, stripe_intent_id: str, status: str) -> None:
    """
    Asynchronously process Stripe webhook events to update payment status in the database.

    Args:
        stripe_intent_id (str): The Stripe PaymentIntent ID.
        status (str): The new payment status (e.g., 'succeeded').
    """
    try:
        service = PaymentService(repository=PaymentRepository())
        updated_payment = service.update_payment_status(
            stripe_intent_id=stripe_intent_id,
            status=status
        )

        if not updated_payment:
            logger.warning(
                "Payment with stripe_intent_id=%s not found in database.",
                stripe_intent_id
            )
        else:
            logger.info(
                "Successfully updated payment status to '%s' for stripe_intent_id=%s",
                status,
                stripe_intent_id
            )

    except Exception as exc:
        logger.error(
            "Error updating payment status for stripe_intent_id=%s: %s",
            stripe_intent_id,
            str(exc)
        )
        raise self.retry(exc=exc)