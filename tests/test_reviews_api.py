from fastapi.testclient import TestClient

from app.main import app
from app.schemas.llm import CsvPreviewResponse, CsvPreviewStats
from app.services.csv_store_service import get_csv_store_service
from app.services.llm_summary_service import get_csv_summary_service
from app.services.playwright_scraper_service import get_playwright_scraper_service

client = TestClient(app)


class MockSummaryService:
    async def summarize(self, _df):
        return CsvPreviewResponse(
            columns=["random_col", "rating"],
            rows=[
                {"random_col": "Great product and fast delivery", "rating": 5},
                {"random_col": "Quality is decent for the price", "rating": 4},
            ],
            stats=CsvPreviewStats(
                row_count=3,
                column_count=2,
                sampled_rows=2,
                null_counts={"random_col": 0, "rating": 0},
                unique_counts={"random_col": 3, "rating": 3},
                column_types={"random_col": "object", "rating": "int64"},
                word_frequencies=[
                    {"word": "great", "count": 1},
                    {"word": "product", "count": 1},
                ],
            ),
        )


class MockStoreService:
    async def save_csv(self, _raw: bytes) -> str:
        return "csv_mock"

    async def get_csv(self, _csv_id: str) -> bytes:
        return b"random_col,rating\nGreat product and fast delivery,5\n"


class MockScraperService:
    async def scrape_reviews(self, _url: str) -> list[str]:
        return ["Great product", "Shipping was slow"]


def test_health_check() -> None:
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_summarize_reviews_csv_success() -> None:
    app.dependency_overrides[get_csv_summary_service] = lambda: MockSummaryService()
    app.dependency_overrides[get_csv_store_service] = lambda: MockStoreService()

    content = (
        "random_col,rating\n"
        "Great product and fast delivery,5\n"
        "Quality is decent for the price,4\n"
        "Not bad,3\n"
    )

    response = client.post(
        "/api/v1/reviews/summarize",
        files={"file": ("reviews.csv", content, "text/csv")},
    )

    app.dependency_overrides.clear()

    assert response.status_code == 200
    payload = response.json()
    assert payload["csv_id"] == "csv_mock"
    assert payload["stats"]["row_count"] == 3
    assert payload["columns"] == ["random_col", "rating"]


def test_summarize_reviews_by_id_success() -> None:
    app.dependency_overrides[get_csv_summary_service] = lambda: MockSummaryService()
    app.dependency_overrides[get_csv_store_service] = lambda: MockStoreService()

    response = client.get("/api/v1/reviews/summarize/csv_mock")

    app.dependency_overrides.clear()

    assert response.status_code == 200
    payload = response.json()
    assert payload["csv_id"] == "csv_mock"


def test_scrape_and_summarize_reviews_success() -> None:
    app.dependency_overrides[get_csv_summary_service] = lambda: MockSummaryService()
    app.dependency_overrides[get_csv_store_service] = lambda: MockStoreService()
    app.dependency_overrides[get_playwright_scraper_service] = lambda: MockScraperService()

    response = client.post(
        "/api/v1/reviews/scrape-summarize",
        json={"url": "https://example.com/reviews"},
    )

    app.dependency_overrides.clear()

    assert response.status_code == 200
    payload = response.json()
    assert payload["csv_id"] == "csv_mock"
    assert payload["scraped_count"] == 2
    assert "preview" in payload


def test_summarize_reviews_csv_invalid_extension() -> None:
    response = client.post(
        "/api/v1/reviews/summarize",
        files={"file": ("reviews.txt", "hello", "text/plain")},
    )

    assert response.status_code == 400
    assert "Only CSV files are accepted" in response.json()["detail"]
