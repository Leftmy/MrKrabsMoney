import json
from unittest.mock import patch

import stripe

from app.models.payment import Payment
from app.tasks.payment_tasks import process_stripe_webhook_task


class TestStripeWebhookEndpoint:
    """Integration tests for POST /api/v1/webhooks/stripe endpoint."""

    def test_webhook_success_triggers_celery_task(self, client, fake_redis_client):
        """Test valid Stripe webhook triggers Celery task asynchronously and returns HTTP 200."""
        payload = {
            "id": "evt_test_123",
            "type": "payment_intent.succeeded",
            "data": {
                "object": {
                    "id": "pi_test_987654321",
                    "status": "succeeded",
                }
            },
        }

        stripe_event = stripe.Event.construct_from(payload, key=None)

        with (
            patch("stripe.Webhook.construct_event") as mock_construct_event,
            patch(
                "app.api.v1.webhook_controller.process_stripe_webhook_task.delay"
            ) as mock_task_delay,
        ):
            mock_construct_event.return_value = stripe_event

            response = client.post(
                "/api/v1/webhooks/stripe",
                data=json.dumps(payload),
                headers={
                    "Content-Type": "application/json",
                    "Stripe-Signature": "t=123,v1=fake_signature",
                },
            )

        assert response.status_code == 200
        assert response.get_json() == {"status": "success"}

        mock_task_delay.assert_called_once_with(
            stripe_intent_id="pi_test_987654321", status="succeeded"
        )

        assert fake_redis_client.exists("webhook:stripe:processed:evt_test_123") == 1

    def test_webhook_invalid_signature_returns_400(self, client):
        """Test invalid signature returns HTTP 400 Bad Request."""
        with patch("stripe.Webhook.construct_event") as mock_construct_event:
            mock_construct_event.side_effect = (
                stripe.error.SignatureVerificationError(
                    "Invalid signature", sig_header="bad_header"
                )
            )

            response = client.post(
                "/api/v1/webhooks/stripe",
                data=json.dumps({"type": "payment_intent.succeeded"}),
                headers={
                    "Content-Type": "application/json",
                    "Stripe-Signature": "invalid_sig",
                },
            )

        assert response.status_code == 400
        data = response.get_json()
        assert "error" in data

    def test_webhook_ignores_unsupported_event_types(self, client, fake_redis_client):
        """Test unsupported event type is acknowledged with HTTP 200 but doesn't trigger Celery task."""
        payload = {
            "id": "evt_test_456",
            "type": "customer.created",
            "data": {"object": {}},
        }

        stripe_event = stripe.Event.construct_from(payload, key=None)

        with (
            patch("stripe.Webhook.construct_event") as mock_construct_event,
            patch(
                "app.api.v1.webhook_controller.process_stripe_webhook_task.delay"
            ) as mock_task_delay,
        ):
            mock_construct_event.return_value = stripe_event

            response = client.post(
                "/api/v1/webhooks/stripe",
                data=json.dumps(payload),
                headers={
                    "Content-Type": "application/json",
                    "Stripe-Signature": "valid_sig",
                },
            )

        assert response.status_code == 200
        mock_task_delay.assert_not_called()


class TestProcessStripeWebhookCeleryTask:
    """Unit tests for process_stripe_webhook_task Celery task."""

    def test_task_updates_payment_status_in_db(self, app, db):
        """Test Celery task finds payment by stripe_intent_id and updates its status in DB."""
        with app.app_context():
            payment = Payment(
                stripe_intent_id="pi_stripe_webhook_test",
                amount_in_cents=2000,
                currency="usd",
                status="pending",
            )
            db.session.add(payment)
            db.session.commit()

        with app.app_context():
            process_stripe_webhook_task(
                stripe_intent_id="pi_stripe_webhook_test", status="succeeded"
            )

        with app.app_context():
            updated_payment = Payment.query.filter_by(
                stripe_intent_id="pi_stripe_webhook_test"
            ).first()
            assert updated_payment is not None
            assert updated_payment.status == "succeeded"

    def test_task_handles_non_existent_stripe_intent_id(self, app):
        """Test Celery task handles non-existent intent ID gracefully without crashing."""
        with app.app_context():
            process_stripe_webhook_task(
                stripe_intent_id="pi_non_existent", status="succeeded"
            )
