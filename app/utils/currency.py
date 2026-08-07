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
    curr = currency.lower().strip()
    d_amount = Decimal(str(amount))

    # Normalize removes trailing zeros (e.g. Decimal('10.500') -> Decimal('10.5'))
    exponent = d_amount.normalize().as_tuple().exponent
    
    if isinstance(exponent, int) and exponent < 0:
        decimal_places = abs(exponent)
        max_allowed = 0 if curr in ZERO_DECIMAL_CURRENCIES else 2

        if decimal_places > max_allowed:
            raise ValueError(
                f"Amount {amount} has {decimal_places} decimal places, "
                f"but currency '{curr}' allows at most {max_allowed}."
            )

    if curr in ZERO_DECIMAL_CURRENCIES:
        return int(d_amount)

    return int(d_amount * Decimal("100"))


def from_stripe_amount(amount_in_cents: int, currency: str = "usd") -> str:
    """Format Stripe integer amount into standard decimal string representation."""
    curr = currency.lower().strip()

    if curr in ZERO_DECIMAL_CURRENCIES:
        return str(amount_in_cents)

    dollars = amount_in_cents // 100
    cents = amount_in_cents % 100
    return f"{dollars}.{cents:02d}"