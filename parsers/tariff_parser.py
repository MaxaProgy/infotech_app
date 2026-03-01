import csv
import io
from datetime import date, time
from decimal import Decimal, InvalidOperation

from engine.models import Tariff


def parse_tariffs(file) -> tuple[list[Tariff], int]:
    """Parse semicolon-delimited tariff file.

    Returns (tariffs, error_count).
    """
    tariffs: list[Tariff] = []
    errors = 0

    if isinstance(file, bytes):
        file = io.StringIO(file.decode("utf-8"))
    elif hasattr(file, "read"):
        content = file.read()
        if isinstance(content, bytes):
            content = content.decode("utf-8")
        file = io.StringIO(content)

    reader = csv.reader(file, delimiter=";")
    for row in reader:
        if not row or all(c.strip() == "" for c in row):
            continue
        if len(row) != 9:
            errors += 1
            continue
        try:
            tariff = Tariff(
                prefix=row[0].strip(),
                destination=row[1].strip(),
                rate_per_min=Decimal(row[2].strip()),
                connection_fee=Decimal(row[3].strip()),
                timeband=_parse_timeband(row[4].strip()),
                weekday=_parse_weekday(row[5].strip()),
                priority=int(row[6].strip()),
                effective_date=date.fromisoformat(row[7].strip()),
                expiry_date=date.fromisoformat(row[8].strip()),
            )
            tariffs.append(tariff)
        except (ValueError, InvalidOperation):
            errors += 1

    return tariffs, errors


def _parse_timeband(s: str) -> tuple[time, time]:
    """Parse '08:00-20:00' → (time(8,0), time(20,0))."""
    start_s, end_s = s.split("-")
    h1, m1 = start_s.split(":")
    h2, m2 = end_s.split(":")
    return time(int(h1), int(m1)), time(int(h2), int(m2))


def _parse_weekday(s: str) -> set[int]:
    """Parse '1-5' → {1,2,3,4,5} or '1,3,5' → {1,3,5}."""
    if "-" in s:
        parts = s.split("-")
        start, end = int(parts[0]), int(parts[1])
        return set(range(start, end + 1))
    return {int(d.strip()) for d in s.split(",")}
