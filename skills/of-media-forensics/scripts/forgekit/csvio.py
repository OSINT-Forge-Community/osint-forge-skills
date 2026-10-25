from __future__ import annotations

import csv
import io

from .safeio import ForgeError, MAX_RECORDS, checkpoint, require


def strict_csv(text, header_code="INVALID_CSV_HEADERS", row_code="INVALID_CSV_ROW"):
    try:
        reader = csv.DictReader(io.StringIO(text, newline=""), strict=True)
        headers = reader.fieldnames
        require(headers is not None and bool(headers) and len(headers) == len(set(headers))
                and all(isinstance(name, str) and bool(name.strip()) for name in headers), header_code)
        rows = []
        for row in reader:
            checkpoint()
            require(len(rows) < MAX_RECORDS, "TOO_MANY_RECORDS")
            require(None not in row and all(value is not None for value in row.values()), row_code)
            rows.append(row)
        return headers, rows
    except csv.Error as exc:
        raise ForgeError("INVALID_CSV_INPUT") from exc
