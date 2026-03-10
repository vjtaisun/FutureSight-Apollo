from fastapi.testclient import TestClient

from app.main import app
from app.schemas.llm import CsvSummaryResponse, CsvSummaryStats
from app.services.csv_store_service import get_csv_store_service
from app.services.llm_summary_service import get_csv_summary_service
from app.services.playwright_scraper_service import get_playwright_scraper_service

client = TestClient(app)


class MockSummaryService:
    async def summarize(self, _df):
        return CsvSummaryResponse(
            summary="Test summary",
            sentiment="positive",
            key_themes=["quality", "delivery"],
            common_issues=["pricing"],
            recommendations=["Improve packaging"],
            stats=CsvSummaryStats(row_count=3, column_count=2, sampled_rows=3),
        )


class MockStoreService:
    def save_csv(self, _raw: bytes) -> str:
        return "csv_mock"

    def get_csv(self, _csv_id: str) -> bytes:
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
    assert payload["summary"] == "Test summary"


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


def test_summarize_reviews_csv_invalid_extension() -> None:
    response = client.post(
        "/api/v1/reviews/summarize",
        files={"file": ("reviews.txt", "hello", "text/plain")},
    )

    assert response.status_code == 400
    assert "Only CSV files are accepted" in response.json()["detail"]
