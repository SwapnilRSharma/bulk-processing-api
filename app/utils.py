import csv
from io import StringIO
from fastapi import UploadFile
from app.config import MAX_CSV_ROWS


def parse_and_validate_csv(file: UploadFile):
    if not file.filename.endswith(".csv"):
        raise ValueError("Only CSV files are allowed")

    content = file.file.read().decode("utf-8")
    reader = csv.DictReader(StringIO(content))

    required = {"name", "address"}
    if not required.issubset(reader.fieldnames):
        raise ValueError("CSV must contain name and address columns")

    rows = list(reader)

    if not rows:
        raise ValueError("CSV file is empty")

    if len(rows) > MAX_CSV_ROWS:
        raise ValueError(f"Maximum {MAX_CSV_ROWS} hospitals allowed")

    return rows
