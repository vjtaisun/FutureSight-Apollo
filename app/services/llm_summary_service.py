import re
from collections import Counter

import pandas as pd

from app.schemas.llm import CsvPreviewResponse, CsvPreviewStats


class CsvSummaryService:
    @staticmethod
    def _sanitize_rows(df: pd.DataFrame) -> list[dict[str, object]]:
        sanitized = df.astype(object).where(pd.notnull(df), None)
        return sanitized.to_dict(orient="records")

    @staticmethod
    def _word_frequencies(df: pd.DataFrame, max_words: int = 200) -> list[dict[str, object]]:
        text_cols = df.select_dtypes(include=["object", "string"]).columns
        if len(text_cols) == 0:
            return []

        counter: Counter[str] = Counter()
        rows = df[text_cols].fillna("").astype(str).agg(" ".join, axis=1)
        for row_text in rows:
            tokens = re.findall(r"[a-z']+", row_text.lower())
            counter.update(token for token in tokens if len(token) >= 3)

        return [{"word": word, "count": count} for word, count in counter.most_common(max_words)]

    async def summarize(self, df: pd.DataFrame) -> CsvPreviewResponse:
        sample_size = 200
        sampled = df.head(sample_size)
        rows = self._sanitize_rows(sampled)
        null_counts = df.isna().sum().to_dict()
        unique_counts = df.nunique(dropna=True).to_dict()
        column_types = {col: str(dtype) for col, dtype in df.dtypes.to_dict().items()}
        word_frequencies = self._word_frequencies(df)

        stats = CsvPreviewStats(
            row_count=int(len(df)),
            column_count=int(len(df.columns)),
            sampled_rows=int(len(sampled)),
            null_counts={str(k): int(v) for k, v in null_counts.items()},
            unique_counts={str(k): int(v) for k, v in unique_counts.items()},
            column_types={str(k): str(v) for k, v in column_types.items()},
            word_frequencies=word_frequencies,
        )

        return CsvPreviewResponse(
            columns=[str(col) for col in df.columns.tolist()],
            rows=rows,
            stats=stats,
        )


_csv_summary_service: CsvSummaryService | None = None


def get_csv_summary_service() -> CsvSummaryService:
    global _csv_summary_service
    if _csv_summary_service is None:
        _csv_summary_service = CsvSummaryService()
    return _csv_summary_service
