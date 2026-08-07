from uuid import UUID
from flask import Blueprint, request, jsonify
from pydantic import ValidationError

from app.schemas.payment_dto import CreatePaymentDTO, PaymentResponseDTO
from app.services.payment_service import PaymentService, PaymentServiceError
from app.repositories.payment_repository import PaymentRepository

payment_bp = Blueprint("payments", __name__, url_prefix="/api/v1/payments")


def get_payment_service() -> PaymentService:
    """Factory helper to initialize PaymentService with its repository."""
    return PaymentService(repository=PaymentRepository())


@payment_bp.route("", methods=["POST"])
def create_payment():
    """
    Create a new payment intent via Stripe and persist it in the database.

    Request Body:
        - amount (float): The monetary value.
        - currency (str): The 3-letter currency code.

    Returns:
        - JSON representation of the payment record with status 201.
        - Error details with appropriate status codes on failure.
    """
    payload = request.get_json() or {}

    # 1. Validate incoming data using Pydantic DTO
    try:
        dto = CreatePaymentDTO(**payload)
    except ValidationError as err:
        return jsonify({"errors": err.errors()}), 400

    # 2. Execute business logic
    service = get_payment_service()
    try:
        payment = service.create_payment(
            amount=dto.amount,
            currency=dto.currency
        )
        response_dto = PaymentResponseDTO.model_validate(payment)
        return jsonify(response_dto.model_dump()), 201

    except ValueError as err:
        return jsonify({"error": str(err)}), 400

    except PaymentServiceError as err:
        return jsonify({"error": str(err)}), 402


@payment_bp.route("/<uuid:payment_id>", methods=["GET"])
def get_payment(payment_id: UUID):
    """
    Retrieve payment details by its primary key UUID.

    Path Parameters:
        - payment_id (UUID): The unique identifier of the payment.

    Returns:
        - JSON representation of the payment record with status 200.
        - 404 error if the payment is not found.
    """
    service = get_payment_service()
    payment = service.get_payment_by_id(payment_id)

    if not payment:
        return jsonify({"error": "Payment not found"}), 404

    response_dto = PaymentResponseDTO.model_validate(payment)
    return jsonify(response_dto.model_dump()), 200
