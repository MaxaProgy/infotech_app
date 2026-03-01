import csv
import io


def parse_subscribers(file) -> tuple[dict[str, str], int]:
    """Parse semicolon-delimited subscriber file.

    Returns (dict[phone_number → name], error_count).
    """
    subscribers: dict[str, str] = {}
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
        if len(row) != 2:
            errors += 1
            continue
        try:
            phone = row[0].strip().lstrip("+")
            name = row[1].strip()
            if phone:
                subscribers[phone] = name
            else:
                errors += 1
        except Exception:
            errors += 1

    return subscribers, errors
