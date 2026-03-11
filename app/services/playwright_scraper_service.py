from __future__ import annotations

import asyncio
import json

from app.core.exceptions import AppError
from app.core.settings import get_settings

REVIEW_LIKE_SELECTORS = [
    '[data-review-id]',
    '[itemprop="reviewBody"]',
    '.review-text',
    '.review',
    '.comment',
    '[data-testid="review-text"]',
    '[data-testid="review"]',
    '[data-testid*="review"]',
    '[data-testid*="Review"]',
    '.review-body',
    '.review__body',
    '.review-content',
    '.reviewText',
    '.review__content',
    '.review__body__text',
    '.review__text',
    '.review-body__text',
    '.reviewBody',
    '[class*="review"]',
    '[data-hook="review-body"]',
    '[data-hook="review-collapsed"]',
]

LOAD_MORE_TEXTS = [
    "Show more",
    "Load more",
    "More reviews",
    "See more",
    "Read more",
    "Show all",
    "View more",
]


class PlaywrightScraperService:
    async def _count_review_nodes(self, page) -> int:
        total = 0
        for selector in REVIEW_LIKE_SELECTORS:
            try:
                total += await page.locator(selector).count()
            except Exception:
                continue
        return total

    async def _scroll_to_load(self, page, max_rounds: int = 12) -> None:
        last_height = 0
        stable_rounds = 0
        for _ in range(max_rounds):
            height = await page.evaluate("() => document.body.scrollHeight")
            if height == last_height:
                stable_rounds += 1
                if stable_rounds >= 2:
                    break
            else:
                stable_rounds = 0
            last_height = height
            await page.evaluate("() => window.scrollTo(0, document.body.scrollHeight)")
            await page.wait_for_timeout(1200)

    async def _click_load_more(self, page) -> None:
        for text in LOAD_MORE_TEXTS:
            locator = page.get_by_role("button", name=text)
            if await locator.count() > 0:
                try:
                    await locator.first.click(timeout=2000)
                    await page.wait_for_timeout(1000)
                except Exception:
                    pass

    async def scrape_reviews(self, url: str) -> list[str]:
        settings = get_settings()
        timeout_ms = settings.request_timeout_seconds * 1000

        try:
            from playwright.async_api import async_playwright  # lazy import
            from bs4 import BeautifulSoup

            async with async_playwright() as p:
                browser = await p.chromium.launch(headless=True)
                context = await browser.new_context()
                page = await context.new_page()
                await page.goto(url, wait_until="networkidle", timeout=timeout_ms)

                # Try to trigger lazy-loaded reviews
                await page.wait_for_timeout(1500)
                await self._click_load_more(page)
                previous_count = await self._count_review_nodes(page)
                for _ in range(4):
                    await self._scroll_to_load(page, max_rounds=10)
                    await self._click_load_more(page)
                    await page.wait_for_timeout(1200)
                    current_count = await self._count_review_nodes(page)
                    if current_count <= previous_count:
                        break
                    previous_count = current_count

                extracted: list[str] = []
                for selector in REVIEW_LIKE_SELECTORS:
                    elements = await page.query_selector_all(selector)
                    for el in elements:
                        text = (await el.inner_text()).strip()
                        if len(text) >= 20:
                            extracted.append(text)

                if not extracted:
                    html = await page.content()
                    soup = BeautifulSoup(html, "lxml")
                    extracted.extend(self._extract_jsonld_reviews(soup))
                    if not extracted:
                        paragraphs = await page.query_selector_all("p")
                        for el in paragraphs:
                            text = (await el.inner_text()).strip()
                            if len(text) >= 60:
                                extracted.append(text)

                await context.close()
                await browser.close()
        except ModuleNotFoundError as exc:
            raise AppError("Playwright is not installed. Run: python -m playwright install", status_code=500) from exc
        except asyncio.TimeoutError as exc:
            raise AppError("Scrape timed out.", status_code=504) from exc
        except Exception as exc:  # noqa: BLE001
            raise AppError(f"Failed to scrape URL: {exc}", status_code=502) from exc

        unique = list(dict.fromkeys(extracted))
        reviews = unique[:200]
        if not reviews:
            raise AppError("No review-like text found on the URL.", status_code=404)
        return reviews

    @staticmethod
    def _extract_jsonld_reviews(soup) -> list[str]:
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


_playwright_scraper_service: PlaywrightScraperService | None = None


def get_playwright_scraper_service() -> PlaywrightScraperService:
    global _playwright_scraper_service
    if _playwright_scraper_service is None:
        _playwright_scraper_service = PlaywrightScraperService()
    return _playwright_scraper_service
