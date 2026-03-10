from pydantic import BaseModel, Field


class CsvSummaryStats(BaseModel):
    row_count: int
    column_count: int
    sampled_rows: int


class CsvSummaryResponse(BaseModel):
    summary: str
    sentiment: str = Field(pattern="^(positive|neutral|negative|mixed)$")
    key_themes: list[str]
    common_issues: list[str]
    recommendations: list[str]
    stats: CsvSummaryStats


class CsvSummaryApiResponse(CsvSummaryResponse):
    csv_id: str


CSV_SUMMARY_JSON_SCHEMA: dict[str, object] = {
    "name": "csv_review_summary",
    "strict": True,
    "schema": {
        "type": "object",
        "additionalProperties": False,
        "required": [
            "summary",
            "sentiment",
            "key_themes",
            "common_issues",
            "recommendations",
            "stats",
        ],
        "properties": {
            "summary": {"type": "string"},
            "sentiment": {
                "type": "string",
                "enum": ["positive", "neutral", "negative", "mixed"],
            },
            "key_themes": {"type": "array", "items": {"type": "string"}},
            "common_issues": {"type": "array", "items": {"type": "string"}},
            "recommendations": {"type": "array", "items": {"type": "string"}},
            "stats": {
                "type": "object",
                "additionalProperties": False,
                "required": ["row_count", "column_count", "sampled_rows"],
                "properties": {
                    "row_count": {"type": "integer"},
                    "column_count": {"type": "integer"},
                    "sampled_rows": {"type": "integer"},
                },
            },
        },
    },
}
