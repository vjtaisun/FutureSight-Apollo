from io import BytesIO

import pandas as pd
from fastapi import UploadFile

from app.core.exceptions import AppError
from app.core.settings import get_settings

ALLOWED_EXTENSIONS = {".csv"}


def validate_csv_file(file: UploadFile) -> None:
    settings = get_settings()
    if not file.filename:
        raise AppError("File name is required.")
    if not any(file.filename.lower().endswith(ext) for ext in ALLOWED_EXTENSIONS):
        raise AppError("Only CSV files are accepted.")

    content_length = file.size or 0
    if content_length > settings.max_csv_size_mb * 1024 * 1024:
        raise AppError(f"CSV file exceeds {settings.max_csv_size_mb}MB limit.")


def load_reviews_dataframe(raw_bytes: bytes) -> pd.DataFrame:
    settings = get_settings()
    try:
        df = pd.read_csv(BytesIO(raw_bytes))
    except Exception as exc:  # noqa: BLE001
        raise AppError(f"Invalid CSV file: {exc}") from exc

    if df.empty:
        raise AppError("CSV is empty.")

    if len(df) > settings.max_rows:
        raise AppError(f"CSV has too many rows. Max allowed is {settings.max_rows}.")

    return df
