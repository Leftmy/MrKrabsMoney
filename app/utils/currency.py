from decimal import Decimal

ZERO_DECIMAL_CURRENCIES = {
    "bif", "clp", "djf", "gnf", "jpy", "kmf", "krw", 
    "mga", "pyg", "rwf", "ugx", "vnd", "vuv", "xaf", "xof", "xpf"
}


def to_stripe_amount(amount: float | Decimal, currency: str = "usd") -> int:
    """
    Convert standard monetary amount to Stripe's minimum integer unit (e.g. cents, yen).
    Raises ValueError if the amount has more decimal places than allowed by the currency.
    """
    ...


def from_stripe_amount(amount_in_cents: int, currency: str = "usd") -> str:
    """Format Stripe integer amount into standard decimal string representation."""
    ...