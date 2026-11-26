from __future__ import annotations

from .llm import LLMExtractor
from .models import ExtractionResult, InvoiceExtraction
from .missing_data import detect_missing
from .duplicate import DuplicateDetector
from .ocr import extract_text_from_bytes

_detector = DuplicateDetector()


def extract_from_text(text: str, use_llm: bool = True) -> ExtractionResult:
    if use_llm:
        extractor = LLMExtractor()
        invoice = extractor.extract(text)
    else:
        from .llm import heuristic_extract

        invoice = heuristic_extract(text)
    invoice.rawText = invoice.rawText or text
    missing = detect_missing(invoice)
    duplicate = _detector.check(invoice)
    return ExtractionResult(invoice=invoice, missingData=missing, duplicate=duplicate, metadata={"textLength": len(text or "")})


def extract_from_file(data: bytes, filename: str, use_llm: bool = True) -> ExtractionResult:
    text = extract_text_from_bytes(data, filename)
    result = extract_from_text(text, use_llm=use_llm)
    result.metadata["filename"] = filename
    result.metadata["ocrAvailable"] = __import__("app.ocr", fromlist=["ocr_available"]).ocr_available()
    result.metadata["extractedTextLength"] = len(text)
    if not text.strip():
        result.metadata["warning"] = (
            "No text could be extracted. For scanned images install Tesseract OCR; "
            "for PDFs ensure they contain selectable text."
        )
    return result