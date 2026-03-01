import io
from datetime import datetime
from decimal import Decimal, InvalidOperation

from engine.models import CdrRecord


def parse_cdr(file) -> tuple[list[CdrRecord], int]:
    """Parse pipe-delimited CDR file.

    Returns (records, error_count).
    """
    records: list[CdrRecord] = []
    errors = 0

    if isinstance(file, bytes):
        file = io.StringIO(file.decode("utf-8"))
    elif hasattr(file, "read"):
        content = file.read()
        if isinstance(content, bytes):
            content = content.decode("utf-8")
        file = io.StringIO(content)

    for line in file:
        line = line.strip()
        if not line:
            continue
        parts = line.split("|")
        if len(parts) != 12:
            errors += 1
            continue
        try:
            record = CdrRecord(
                start_time=datetime.strptime(parts[0].strip(), "%Y-%m-%d %H:%M:%S"),
                end_time=datetime.strptime(parts[1].strip(), "%Y-%m-%d %H:%M:%S"),
                calling_party=_normalize_number(parts[2].strip()),
                called_party=_normalize_number(parts[3].strip()),
                call_direction=parts[4].strip().lower(),
                disposition=parts[5].strip().lower(),
                duration=int(parts[6].strip()),
                billable_sec=int(parts[7].strip()),
                charge=Decimal(parts[8].strip()),
                account_code=parts[9].strip(),
                call_id=parts[10].strip(),
                trunk_name=parts[11].strip(),
            )
            records.append(record)
        except (ValueError, InvalidOperation):
            errors += 1

    return records, errors


def _normalize_number(number: str) -> str:
    return number.lstrip("+")
