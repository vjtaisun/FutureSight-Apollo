from uuid import uuid4

from app.core.exceptions import AppError
from app.services.openai_client import OpenAIClient, get_openai_client


class CsvStoreService:
    def __init__(
        self,
        client: OpenAIClient | None = None,
    ) -> None:
        self.client = client or get_openai_client()

    async def save_csv(self, raw_bytes: bytes) -> str:
        try:
            filename = f"{uuid4().hex}.csv"
            openai_file = await self.client.files_create_bytes(raw_bytes, filename)
            vector_store = await self.client.vector_store_create(
                name=f"csv-{filename.removesuffix('.csv')}",
                file_ids=[str(getattr(openai_file, "id", ""))],
            )
        except Exception as exc:  # noqa: BLE001
            raise AppError(f"Vector store creation failed: {exc}", status_code=502) from exc

        vector_store_id = getattr(vector_store, "id", None)
        if not vector_store_id:
            raise AppError("Vector store id missing from OpenAI response.", status_code=502)

        return str(vector_store_id)

    async def get_csv(self, csv_id: str) -> bytes:
        try:
            files_page = await self.client.vector_store_files_list(csv_id)
        except Exception as exc:  # noqa: BLE001
            raise AppError(f"Vector store lookup failed: {exc}", status_code=502) from exc

        data = getattr(files_page, "data", None)
        if not data:
            raise AppError("No files found in vector store.", status_code=404)

        file_id = getattr(data[0], "id", None)
        if not file_id:
            raise AppError("Vector store file id missing.", status_code=404)

        try:
            return await self.client.files_content(str(file_id))
        except Exception as exc:  # noqa: BLE001
            raise AppError(f"Failed to download CSV content: {exc}", status_code=502) from exc


_csv_store_service: CsvStoreService | None = None


def get_csv_store_service() -> CsvStoreService:
    global _csv_store_service
    if _csv_store_service is None:
        _csv_store_service = CsvStoreService()
    return _csv_store_service
