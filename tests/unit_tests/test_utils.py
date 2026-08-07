from decimal import Decimal
import pytest
from app.utils.currency import to_stripe_amount, from_stripe_amount


# --- Tests for to_stripe_amount ---

def test_to_stripe_amount_standard_currency():
    """Test standard currency conversion (USD, EUR) into cents."""
    assert to_stripe_amount(15.15, "usd") == 1515
    assert to_stripe_amount(Decimal("10.50"), "EUR") == 1050


def test_to_stripe_amount_zero_decimal_currency():
    """Test zero-decimal currencies (JPY, KRW) without multiplying by 100."""
    assert to_stripe_amount(500, "jpy") == 500
    assert to_stripe_amount(Decimal("1500"), "KRW") == 1500


def test_to_stripe_amount_raises_error_for_excess_decimals():
    """Test that amounts with more than 2 decimal places raise ValueError."""
    with pytest.raises(ValueError, match="allows at most 2"):
        to_stripe_amount(10.125, "usd")

    with pytest.raises(ValueError, match="allows at most 2"):
        to_stripe_amount(Decimal("15.154"), "EUR")


def test_to_stripe_amount_raises_error_for_zero_decimal_fraction():
    """Test that zero-decimal currencies with fractional amounts raise ValueError."""
    with pytest.raises(ValueError, match="allows at most 0"):
        to_stripe_amount(500.5, "jpy")


# --- Tests for from_stripe_amount ---

def test_from_stripe_amount_standard_currency():
    """Test converting integer cents back to standard decimal string."""
    assert from_stripe_amount(1515, "usd") == "15.15"


def test_from_stripe_amount_single_digit_and_zero_cents():
    """Test padding for amounts with less than 10 cents."""
    assert from_stripe_amount(5, "usd") == "0.05"
    assert from_stripe_amount(0, "usd") == "0.00"


def test_from_stripe_amount_zero_decimal_currency():
    """Test formatting zero-decimal currencies without decimal point."""
    assert from_stripe_amount(500, "  JPY ") == "500"