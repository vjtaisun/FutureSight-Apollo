import json

import pandas as pd

from app.core.exceptions import AppError
from app.prompts.csv_summary_prompt import get_csv_summary_prompts
from app.schemas.llm import CSV_SUMMARY_JSON_SCHEMA, CsvSummaryResponse
from app.services.openai_client import OpenAIClient, get_openai_client


class CsvSummaryService:
    def __init__(self, client: OpenAIClient | None = None) -> None:
        self.client = client or get_openai_client()
        self.default_model = self.client.default_model

    @staticmethod
    def _build_context(df: pd.DataFrame, sample_size: int = 200) -> dict[str, object]:
        sampled = df.head(sample_size)
        return {
            "columns": df.columns.tolist(),
            "row_count": int(len(df)),
            "column_count": int(len(df.columns)),
            "sampled_rows": int(len(sampled)),
            "rows": sampled.to_dict(orient="records"),
        }

    async def _call_llm(self, model: str, system_prompt: str, context: str):
        return await self.client.responses_create(
            model=model,
            input=[
                {
                    "role": "system",
                    "content": [{"type": "input_text", "text": system_prompt}],
                },
                {
                    "role": "user",
                    "content": [
                        {"type": "input_text", "text": context},
                    ],
                },
            ],
            text={
                "format": {
                    "type": "json_schema",
                    "json_schema": CSV_SUMMARY_JSON_SCHEMA,
                }
            },
        )

    async def _call_llm_json_object(
        self, model: str, system_prompt: str, context: str
    ):
        return await self.client.responses_create(
            model=model,
            input=[
                {
                    "role": "system",
                    "content": [{"type": "input_text", "text": system_prompt}],
                },
                {
                    "role": "user",
                    "content": [
                        {"type": "input_text", "text": context},
                    ],
                },
            ],
            text={"format": {"type": "json_object"}},
        )

    async def summarize(self, df: pd.DataFrame) -> CsvSummaryResponse:
        system_prompt = get_csv_summary_prompts()
        context = json.dumps(self._build_context(df), ensure_ascii=True)
        model = self.default_model

        try:
            response = await self._call_llm(model, system_prompt, context)
        except Exception:
            response = await self._call_llm_json_object(model, system_prompt, context)

        output_text = getattr(response, "output_text", None)
        if not output_text:
            raise AppError("LLM did not return output text.", status_code=502)

        try:
            payload = json.loads(output_text)
        except json.JSONDecodeError as exc:
            raise AppError("LLM returned invalid JSON.", status_code=502) from exc

        return CsvSummaryResponse(**payload)


_csv_summary_service: CsvSummaryService | None = None


def get_csv_summary_service() -> CsvSummaryService:
    global _csv_summary_service
    if _csv_summary_service is None:
        _csv_summary_service = CsvSummaryService()
    return _csv_summary_service
