import json
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
    '.review-body',
    '.review__body',
    '.review-content',
    '.reviewText',
    '[data-hook="review-body"]',
    '[data-hook="review-collapsed"]',
]


def _extract_jsonld_reviews(soup: BeautifulSoup) -> list[str]:
    extracted: list[str] = []
    scripts = soup.find_all("script", attrs={"type": "application/ld+json"})
    for script in scripts:
        try:
            payload = json.loads(script.string or "")
        except Exception:
            continue

        nodes = payload if isinstance(payload, list) else [payload]
        for node in nodes:
            graph = node.get("@graph") if isinstance(node, dict) else None
            for item in (graph or [node]):
                if not isinstance(item, dict):
                    continue
                reviews = item.get("review") or item.get("reviews") or []
                if isinstance(reviews, dict):
                    reviews = [reviews]
                for review in reviews:
                    if not isinstance(review, dict):
                        continue
                    body = review.get("reviewBody")
                    if isinstance(body, str) and len(body) >= 20:
                        extracted.append(body.strip())
    return extracted


def _extract_text_candidates(soup: BeautifulSoup) -> list[str]:
    extracted: list[str] = []

    extracted.extend(_extract_jsonld_reviews(soup))

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
