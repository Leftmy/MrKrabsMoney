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


@payment_bp.route("/payments", methods=["POST"])
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
    ...


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
    ...