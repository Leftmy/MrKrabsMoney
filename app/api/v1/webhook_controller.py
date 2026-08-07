from flask import Blueprint, request, jsonify, current_app
import stripe
import redis

from app.tasks.payment_tasks import process_stripe_webhook_task

webhook_bp = Blueprint("webhooks", __name__, url_prefix="/api/v1/webhooks")


def get_redis_client():
    return redis.Redis.from_url(current_app.config["REDIS_URL"], decode_responses=True)

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

    redis_client = get_redis_client()
    event_id = event.id
    redis_key = f"webhook:stripe:processed:{event_id}"

    is_new_event = redis_client.set(redis_key, "processing", nx=True, ex=259200) # 3 days expiration

    if not is_new_event:
        return jsonify({"status": "ignored", "reason": "Duplicate event"}), 200


    event_type = event.type
    data_object = event.data.object

    if event_type in ("payment_intent.succeeded", "payment_intent.payment_failed"):
        stripe_intent_id = getattr(data_object, "id", None)
        status = getattr(data_object, "status", None)

        if stripe_intent_id and status:
            process_stripe_webhook_task.delay(
                stripe_intent_id=stripe_intent_id,
                status=status
            )

    return jsonify({"status": "success"}), 200