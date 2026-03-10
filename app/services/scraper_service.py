from typing import Any

import httpx
from bs4 import BeautifulSoup

from app.core.exceptions import AppError
from app.core.settings import get_settings

REVIEW_LIKE_SELECTORS = [
    '[data-review-id]',
    '[itemprop="reviewBody"]',
    '.review-text',
    '.review',
    '.comment',
]


def _extract_text_candidates(soup: BeautifulSoup) -> list[str]:
    extracted: list[str] = []

    for selector in REVIEW_LIKE_SELECTORS:
        nodes = soup.select(selector)
        for node in nodes:
            text = node.get_text(strip=True)
            if len(text) >= 20:
                extracted.append(text)

    if not extracted:
        for paragraph in soup.find_all("p"):
            text = paragraph.get_text(strip=True)
            if len(text) >= 60:
                extracted.append(text)

    unique = list(dict.fromkeys(extracted))
    return unique[:200]


async def scrape_review_text(url: str) -> list[str]:
    settings = get_settings()
    timeout = httpx.Timeout(settings.request_timeout_seconds)
    headers: dict[str, Any] = {
        "User-Agent": "Mozilla/5.0 (compatible; ReviewSummarizerBot/1.0)",
    }

    try:
        async with httpx.AsyncClient(timeout=timeout, follow_redirects=True, headers=headers) as client:
            response = await client.get(url)
            response.raise_for_status()
    except httpx.HTTPError as exc:
        raise AppError(f"Failed to fetch URL: {exc}", status_code=502) from exc

    soup = BeautifulSoup(response.text, "lxml")
    reviews = _extract_text_candidates(soup)

    if not reviews:
        raise AppError("No review-like text found on the URL.", status_code=404)

    return reviews
