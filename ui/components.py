import math
from decimal import Decimal


def format_duration(seconds: int) -> str:
    """Format seconds as MM:SS."""
    m, s = divmod(seconds, 60)
    return f"{m}:{s:02d}"


def format_money(value: Decimal | None) -> str:
    if value is None:
        return "—"
    return f"{value:.2f}"


def format_minutes(seconds: int) -> str:
    return str(math.ceil(seconds / 60))
