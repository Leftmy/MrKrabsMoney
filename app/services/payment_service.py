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
    ...


class PaymentService:
    """Service layer handling payment processing logic and Stripe API integration."""
    
    def __init__(self, repository: Optional[PaymentRepository] = None):
        pass