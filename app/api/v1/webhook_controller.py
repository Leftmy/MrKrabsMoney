from flask import Blueprint, request, jsonify, current_app
import stripe

from app.tasks.payment_tasks import process_stripe_webhook_task

webhook_bp = Blueprint("webhooks", __name__, url_prefix="/webhooks")


@webhook_bp.route("/stripe", methods=["POST"])
def stripe_webhook():
    """
    Handle incoming Stripe webhook events.
    
    Verifies event signature and delegates background database processing to Celery task.
    """
    payload = request.get_data()
    sig_header = request.headers.get("Stripe-Signature")
    endpoint_secret = current_app.config.get("STRIPE_WEBHOOK_SECRET")

    try:
        if endpoint_secret:
            event = stripe.Webhook.construct_event(
                payload=payload,
                sig_header=sig_header,
                secret=endpoint_secret
            )
        else:
            # Fallback for local dev/testing mode without secret
            event = stripe.Event.construct_from(
                request.get_json(force=True), stripe.api_key
            )
    except (ValueError, stripe.error.SignatureVerificationError) as err:
        return jsonify({"error": f"Invalid webhook payload or signature: {str(err)}"}), 400

    event_type = event.get("type")
    data_object = event.get("data", {}).get("object", {})

    # We only process relevant payment intent events
    if event_type in ("payment_intent.succeeded", "payment_intent.payment_failed"):
        stripe_intent_id = data_object.get("id")
        status = data_object.get("status")

        if stripe_intent_id and status:
            process_stripe_webhook_task.delay(
                stripe_intent_id=stripe_intent_id,
                status=status
            )

    return jsonify({"status": "success"}), 200