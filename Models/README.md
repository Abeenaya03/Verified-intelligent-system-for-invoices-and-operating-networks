# Member 1 - OCR & LLM Extraction Service

Implements Task Description 1:
1. OCR Integration - read text from uploaded invoice/PO documents (optional pytesseract/pdfplumber; graceful fallback).
2. LLM Integration - OpenAI-based extraction when API key is configured, otherwise a deterministic heuristic fallback.
3. Data Extraction - supplier, invoice number, PO number, dates, items, quantities, prices, tax, total.
4. Structured JSON - pydantic-validated `InvoiceExtraction` model.
5. Missing Data Detection - flags missing/unreadable required fields.
6. Model Testing - `scripts/model_testing.py` evaluates extraction across sample formats.
7. Duplicate Detection - fingerprint + similarity based duplicate check.

## Run
```bash
cd member1
python -m uvicorn app.main:app --reload --port 8001
```

## Test
```bash
cd member1
python -m pytest -q
python scripts/model_testing.py
```

## Endpoints
- `GET /health`
- `POST /extract` (multipart: invoice file, optional po file)
- `POST /extract-text` (JSON: { "text": "...", "use_llm": false })
- `POST /duplicate-check` (JSON invoice)
- `POST /register` (register invoice for future duplicate checks)