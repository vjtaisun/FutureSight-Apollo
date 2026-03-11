from fastapi import APIRouter, Depends, File, UploadFile

from app.core.exceptions import AppError
from app.schemas.llm import CsvPreviewApiResponse
from app.schemas.reviews import (
    ScrapeRequest,
    ScrapeResponse,
    ScrapeSummarizeRequest,
    ScrapeSummarizeResponse,
)
from app.services.csv_service import load_reviews_dataframe, validate_csv_file
from app.services.csv_store_service import CsvStoreService, get_csv_store_service
from app.services.llm_summary_service import CsvSummaryService, get_csv_summary_service
from app.services.playwright_scraper_service import (
    PlaywrightScraperService,
    get_playwright_scraper_service,
)
from app.services.scraper_service import scrape_review_text

router = APIRouter()


@router.post("/reviews/summarize", response_model=CsvPreviewApiResponse)
async def summarize_reviews_csv(
    file: UploadFile = File(...),
    summary_service: CsvSummaryService = Depends(get_csv_summary_service),
    store_service: CsvStoreService = Depends(get_csv_store_service),
) -> CsvPreviewApiResponse:
    validate_csv_file(file)
    raw = await file.read()

    csv_id = await store_service.save_csv(raw)
    df = load_reviews_dataframe(raw)
    summary = await summary_service.summarize(df)

    return CsvPreviewApiResponse(csv_id=csv_id, **summary.model_dump())


@router.get("/reviews/summarize/{csv_id}", response_model=CsvPreviewApiResponse)
async def summarize_reviews_by_id(
    csv_id: str,
    summary_service: CsvSummaryService = Depends(get_csv_summary_service),
    store_service: CsvStoreService = Depends(get_csv_store_service),
) -> CsvPreviewApiResponse:
    raw = await store_service.get_csv(csv_id)
    df = load_reviews_dataframe(raw)
    summary = await summary_service.summarize(df)
    return CsvPreviewApiResponse(csv_id=csv_id, **summary.model_dump())


@router.post("/reviews/scrape", response_model=ScrapeResponse)
async def scrape_reviews(
    payload: ScrapeRequest,
    scraper_service: PlaywrightScraperService = Depends(get_playwright_scraper_service),
) -> ScrapeResponse:
    url = str(payload.url)
    try:
        reviews = await scraper_service.scrape_reviews(url)
    except AppError as exc:
        if exc.status_code in (404, 500):
            reviews = await scrape_review_text(url)
        else:
            raise
    return ScrapeResponse(url=str(payload.url), extracted_reviews=reviews, count=len(reviews))


@router.post("/reviews/scrape-summarize", response_model=ScrapeSummarizeResponse)
async def scrape_and_summarize_reviews(
    payload: ScrapeSummarizeRequest,
    summary_service: CsvSummaryService = Depends(get_csv_summary_service),
    store_service: CsvStoreService = Depends(get_csv_store_service),
    scraper_service: PlaywrightScraperService = Depends(get_playwright_scraper_service),
) -> ScrapeSummarizeResponse:
    url = str(payload.url)
    reviews = await scraper_service.scrape_reviews(url)
    csv_bytes = ("review\n" + "\n".join(r.replace("\n", " ") for r in reviews)).encode(
        "utf-8"
    )
    csv_id = await store_service.save_csv(csv_bytes)

    df = load_reviews_dataframe(csv_bytes)
    summary = await summary_service.summarize(df)

    return ScrapeSummarizeResponse(
        url=str(payload.url),
        csv_id=csv_id,
        scraped_count=len(reviews),
        preview=summary.model_dump(),
    )
