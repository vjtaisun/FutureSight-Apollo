from pydantic import BaseModel


class WordFrequency(BaseModel):
    word: str
    count: int


class CsvPreviewStats(BaseModel):
    row_count: int
    column_count: int
    sampled_rows: int
    null_counts: dict[str, int]
    unique_counts: dict[str, int]
    column_types: dict[str, str]
    word_frequencies: list[WordFrequency]


class CsvPreviewResponse(BaseModel):
    columns: list[str]
    rows: list[dict[str, object]]
    stats: CsvPreviewStats


class CsvPreviewApiResponse(CsvPreviewResponse):
    csv_id: str
