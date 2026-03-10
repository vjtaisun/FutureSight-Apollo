import json
import time
from pathlib import Path
from uuid import uuid4

from app.core.exceptions import AppError


class CsvStoreService:
    def __init__(self, base_dir: Path | None = None, max_items: int = 10) -> None:
        self.base_dir = base_dir or Path("/Users/nishameena/Desktop/FutureFirstAI-Apollo/data/csv_store")
        self.base_dir.mkdir(parents=True, exist_ok=True)
        self.index_path = self.base_dir / "index.json"
        self.max_items = max_items

    def _load_index(self) -> list[dict[str, object]]:
        if not self.index_path.exists():
            return []
        try:
            data = json.loads(self.index_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            return []
        if not isinstance(data, list):
            return []
        return data

    def _save_index(self, items: list[dict[str, object]]) -> None:
        self.index_path.write_text(json.dumps(items, indent=2), encoding="utf-8")

    def _evict_if_needed(self, items: list[dict[str, object]]) -> list[dict[str, object]]:
        if len(items) <= self.max_items:
            return items
        items.sort(key=lambda x: x.get("created_at", 0))
        while len(items) > self.max_items:
            oldest = items.pop(0)
            file_path = self.base_dir / str(oldest.get("filename", ""))
            if file_path.exists():
                file_path.unlink()
        return items

    def save_csv(self, raw_bytes: bytes) -> str:
        csv_id = f"csv_{uuid4().hex}"
        filename = f"{csv_id}.csv"
        file_path = self.base_dir / filename
        file_path.write_bytes(raw_bytes)

        items = self._load_index()
        items.append({"id": csv_id, "filename": filename, "created_at": int(time.time())})
        items = self._evict_if_needed(items)
        self._save_index(items)
        return csv_id

    def get_csv(self, csv_id: str) -> bytes:
        items = self._load_index()
        match = next((item for item in items if item.get("id") == csv_id), None)
        if not match:
            raise AppError("CSV id not found.", status_code=404)
        file_path = self.base_dir / str(match.get("filename"))
        if not file_path.exists():
            raise AppError("CSV file missing on disk.", status_code=404)
        return file_path.read_bytes()


_csv_store_service: CsvStoreService | None = None


def get_csv_store_service() -> CsvStoreService:
    global _csv_store_service
    if _csv_store_service is None:
        _csv_store_service = CsvStoreService()
    return _csv_store_service
