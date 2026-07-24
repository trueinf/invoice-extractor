# Invoice Extraction Service

End-to-end invoice extraction application built for structured JSON extraction from PDFs and images.

This repo is now split for Netlify: the static frontend lives in `frontend/`, and the extraction API is deployed separately.

## What it does

- accepts PDF and image uploads
- extracts text with PDF parsing or OCR
- applies invoice heuristics
- optionally calls an OpenAI-compatible LLM for structured JSON extraction
- normalizes dates and numeric fields
- validates arithmetic totals
- computes section confidence
- persists jobs in SQLite
- stores uploaded files on disk
- supports async job processing and sync extraction
- serves a browser UI and JSON API

## Run locally

### Backend

```bash
cp .env.example .env
python -m venv .venv
source .venv/bin/activate
pip install -e .
uvicorn app.main:app --reload
```

### Frontend

Serve the `frontend/` folder with any static server or open it from a dev server.
Set the backend API URL in the settings panel at the top of the page.

For tests:

```bash
pip install -e .[dev]
pytest
```

Or use the CLI:

```bash
invoice-extractor path/to/invoice.pdf
```

For the frontend, deploy `frontend/` to Netlify or open it from any static server.

## Run with Docker

```bash
docker build -t invoice-extractor .
docker run --rm -p 8000:8000 --env-file .env -v $(pwd)/data:/app/data invoice-extractor
```

Or with Compose:

```bash
docker compose up --build
```

## Netlify deployment

1. Deploy the `frontend/` folder to Netlify as the static site.
2. Deploy the backend API to a Python host of your choice.
3. Set `CORS_ORIGINS` on the backend to your Netlify domain.
4. Open the Netlify site and enter the backend API base URL in the settings panel.

Netlify only serves the UI. The backend still does OCR, validation, persistence, and extraction.

## Production API

- `POST /v1/extractions` — create an async extraction job
- `GET /v1/extractions/{job_id}` — check job status
- `GET /v1/extractions/{job_id}/result` — fetch completed JSON
- `POST /v1/extractions/sync` — extract immediately and return the result
- `GET /health/live` — liveness
- `GET /health/ready` — readiness

If your frontend is on Netlify, set the backend to allow CORS from the Netlify domain using `CORS_ORIGINS`.

Open:

- http://127.0.0.1:8000/ for the UI
- http://127.0.0.1:8000/docs for the API docs

## Environment variables

- `DATA_DIR` — directory for uploads and app data, default `./data`
- `DATABASE_PATH` — SQLite database path, default `./data/app.db`
- `LLM_BASE_URL` — OpenAI-compatible base URL, for example `https://api.openai.com/v1`
- `LLM_API_KEY` — bearer token for the LLM provider
- `LLM_MODEL` — model name
- `ENABLE_OCR` — `true` or `false`
- `OCR_LANGUAGE` — Tesseract OCR language code, default `eng`
- `MAX_UPLOAD_BYTES` — upload limit in bytes
- `MIN_CONFIDENCE_HIGH` / `MIN_CONFIDENCE_MEDIUM` — confidence thresholds
- `CORS_ORIGINS` — comma-separated allowed origins for the Netlify frontend, default `*`

## Architecture

1. Upload invoice file
2. Extract raw text from PDF or image
3. Run heuristic extraction
4. Optionally refine with an LLM
5. Normalize values
6. Validate arithmetic and flag anomalies
7. Return structured JSON

## Notes

- The app is designed to work even without an LLM, but accuracy improves significantly when one is configured.
- Scanned PDFs are OCRed through PyMuPDF + Tesseract when both are available.
- SQLite is the default job store; switch to a managed Postgres-backed implementation if you need multi-instance writes at scale.
