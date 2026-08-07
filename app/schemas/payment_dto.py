from uuid import UUID
from pydantic import BaseModel, Field, field_validator


class CreatePaymentDTO(BaseModel):
    """Data Transfer Object for creating a new payment."""
    
    amount: float = Field(..., gt=0, description="Monetary amount (e.g. 15.15)")
    currency: str = Field(..., min_length=3, max_length=3, description="3-letter ISO currency code (e.g. usd, jpy)")

    @field_validator("currency")
    @classmethod
    def normalize_currency(cls, v: str) -> str:
        """Normalize currency code to lowercase and strip whitespace."""
        return v.lower().strip()


class PaymentResponseDTO(BaseModel):
    """Data Transfer Object representing a payment response."""
    
    id: UUID
    stripe_intent_id: str
    amount_in_cents: int
    currency: str
    status: str

    model_config = {
        "from_attributes": True
    }