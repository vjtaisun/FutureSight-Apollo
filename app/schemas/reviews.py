from pydantic import BaseModel, Field, HttpUrl


class SummaryStats(BaseModel):
    total_reviews: int
    average_rating: float | None = None
    ratings_distribution: dict[str, int]
    top_keywords: list[str]


class SummaryResponse(BaseModel):
    summary: str
    stats: SummaryStats


class ScrapeRequest(BaseModel):
    url: HttpUrl


class ScrapeResponse(BaseModel):
    url: str
    extracted_reviews: list[str] = Field(default_factory=list)
    count: int


class ScrapeSummarizeRequest(BaseModel):
    url: HttpUrl


class ScrapeSummarizeResponse(BaseModel):
    url: str
    csv_id: str
    scraped_count: int
    preview: dict[str, object]
