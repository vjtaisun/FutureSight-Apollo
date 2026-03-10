# Review Summarizer Backend

Production-oriented FastAPI backend for:
- Uploading CSV files with product/business reviews
- Processing and summarizing reviews
- Optional scraping endpoint to extract review-like text from a URL
- AI chat assistant streaming via OpenAI Responses API

## Project Structure

```
app/
  api/
    v1/
      routes_chat.py
      routes_reviews.py
    router.py
  core/
    exceptions.py
    logging.py
    settings.py
  prompts/
    chat_csv_context_prompt.py
    csv_summary_prompt.py
    system_prompt.py
  schemas/
    chat.py
    llm.py
    reviews.py
  services/
    chat_service.py
    csv_service.py
    csv_store_service.py
    llm_summary_service.py
    openai_client.py
    playwright_scraper_service.py
    scraper_service.py
    summarizer_service.py
  main.py
tests/
  test_chat_api.py
  test_reviews_api.py
data/
  csv_store/
```

## Run (Local)

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e '.[dev]'
python -m playwright install
cp .env.example .env
uvicorn app.main:app --reload
```

## API Endpoints

- `GET /health`
- `POST /api/v1/reviews/summarize`
  - multipart form-data with `file=<csv>`
  - LLM-based summary across arbitrary columns
  - Returns a `csv_id` for later reuse
- `GET /api/v1/reviews/summarize/{csv_id}`
  - Re-summarize a previously uploaded CSV
- `POST /api/v1/reviews/scrape`
  - JSON body: `{ "url": "https://example.com" }`
- `POST /api/v1/reviews/scrape-summarize`
  - JSON body: `{ "url": "https://example.com" }`
  - Scrapes with Playwright, saves CSV, returns `csv_id` and summary
- `POST /api/v1/chat/stream`
  - JSON body with chat message
  - SSE response (`text/event-stream`)

## CSV Summary Output Schema

```json
{
  "csv_id": "csv_...",
  "summary": "...",
  "sentiment": "positive|neutral|negative|mixed",
  "key_themes": ["..."],
  "common_issues": ["..."],
  "recommendations": ["..."],
  "stats": {
    "row_count": 100,
    "column_count": 5,
    "sampled_rows": 100
  }
}
```

## Storage Notes

- Up to 10 CSV files are stored locally in `data/csv_store`.
- When more than 10 files are uploaded, the oldest files are removed automatically.
- The frontend should persist `csv_id` and pass it to `/reviews/summarize/{csv_id}` when needed.

## Chat Streaming Payload

```json
{
  "message": "Summarize these reviews and focus on product quality",
  "csv_id": "csv_abc123",
  "model": "gpt-4.1-mini",
  "temperature": 0.2,
  "max_output_tokens": 700,
  "previous_response_id": "resp_abc123"
}
```

SSE events emitted:
- `token`: incremental text chunks (`{"text":"..."}`)
- `done`: final metadata and token usage (`{"response_id":"resp_..."}` included)
- `error`: upstream model error

## Notes for Production

- Reverse proxy (Nginx/ALB) and TLS termination should be configured externally.
- For SSE, disable proxy buffering (`X-Accel-Buffering: no`) and increase upstream timeouts.
- Add distributed rate limiting and request quotas for public APIs.
- Respect robots.txt and site ToS for scraping.

## Railway Deployment

### Required Environment Variables
- `OPENAI_API_KEY`
- `OPENAI_MODEL` (default: `gpt-4.1-mini`)
- `CSV_STORE_DIR` (default: `data/csv_store`)

Use `.env.example` as a template for all supported settings.

### Build and Start
- Build command (install Playwright browsers):
  - `python -m playwright install --with-deps`
- Start command:
  - `uvicorn app.main:app --host 0.0.0.0 --port $PORT`

### Storage
CSV uploads are stored on disk. Railway storage is ephemeral unless you attach a volume. If you need CSVs to survive deploys or restarts, add a Railway volume and set `CSV_STORE_DIR` to the mounted path. If you only need short-lived storage (up to 10 files), ephemeral storage is acceptable.

### Packaging
This project uses `pyproject.toml` as the source of truth for dependencies. Prefer installing with:
- `pip install .` (prod)
- `pip install -e '.[dev]'` (dev)
