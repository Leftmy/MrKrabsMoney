from enum import Enum
from datetime import datetime, timezone
import uuid
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import String, Integer, DateTime, Uuid
from app.extensions import db


class PaymentStatus(str, Enum):
    """Enumeration of possible payment statuses."""
    PENDING = "pending"
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    CANCELED = "canceled"


class Payment(db.Model):
    """Database model representing a payment transaction using SQLAlchemy 2.0 syntax."""
    __tablename__ = "payments"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4
    )
    stripe_intent_id: Mapped[str] = mapped_column(
        String(255),
        unique=True,
        nullable=False,
        index=True
    )
    amount_in_cents: Mapped[int] = mapped_column(
        Integer,
        nullable=False
    )
    currency: Mapped[str] = mapped_column(
        String(10),
        nullable=False,
        default="usd"
    )
    status: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default=PaymentStatus.PENDING.value
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc)
    )

    def __repr__(self) -> str:
        return f"<Payment id='{self.id}' stripe_intent_id='{self.stripe_intent_id}' status='{self.status}'>"
