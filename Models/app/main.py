from __future__ import annotations

import io
from typing import Optional

from fastapi import FastAPI, File, Form, UploadFile, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from .extraction import extract_from_file, extract_from_text
from .models import DuplicateResult, ExtractionResult, InvoiceExtraction
from .duplicate import DuplicateDetector

app = FastAPI(title="V.I.S.I.O.N Member 1 - OCR/LLM Extraction", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

_detector = DuplicateDetector()


@app.get("/health")
def health():
    from .ocr import ocr_available

    return {"status": "ok", "ocrAvailable": ocr_available()}


@app.post("/extract-text", response_model=ExtractionResult)
def extract_text(payload: dict):
    text = payload.get("text", "")
    use_llm = bool(payload.get("use_llm", True))
    return extract_from_text(text, use_llm=use_llm)


@app.post("/extract", response_model=ExtractionResult)
async def extract(invoice: UploadFile = File(...), po: Optional[UploadFile] = File(None), use_llm: bool = Form(True)):
    data = await invoice.read()
    result = extract_from_file(data, invoice.filename or "invoice", use_llm=use_llm)
    if po is not None:
        po_data = await po.read()
        # store PO text in metadata only (extraction focuses on invoice)
        result.metadata["poFilename"] = po.filename
        result.metadata["poTextLength"] = len(__import__("app.ocr", fromlist=["extract_text_from_bytes"]).extract_text_from_bytes(po_data, po.filename or "po"))
    return result


@app.post("/duplicate-check", response_model=DuplicateResult)
def duplicate_check(invoice: InvoiceExtraction):
    return _detector.check(invoice)


@app.post("/register")
def register(invoice: InvoiceExtraction, invoice_id: str = "manual"):
    _detector.register(invoice, invoice_id)
    return {"registered": True, "invoice_id": invoice_id}