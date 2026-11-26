from __future__ import annotations

import io
from typing import Optional

try:
    import pytesseract  # type: ignore
    from PIL import Image  # type: ignore

    _TESSERACT = True
except Exception:  # pragma: no cover - optional dependency
    pytesseract = None
    Image = None
    _TESSERACT = False

try:
    import pdfplumber  # type: ignore

    _PDFPLUMBER = True
except Exception:  # pragma: no cover - optional dependency
    pdfplumber = None
    _PDFPLUMBER = False

try:
    from pypdf import PdfReader  # type: ignore

    _PYPDF = True
except Exception:  # pragma: no cover - optional dependency
    try:
        from PyPDF2 import PdfReader  # type: ignore

        _PYPDF = True
    except Exception:
        PdfReader = None
        _PYPDF = False


def extract_text_from_bytes(data: bytes, filename: str) -> str:
    """Extract text from an uploaded file (image, PDF, or plain text). Falls back to empty string."""
    name = (filename or "").lower()
    text_parts: list[str] = []

    # Plain text handling
    if name.endswith((".txt", ".text", ".csv", ".json", ".md")):
        try:
            return data.decode("utf-8", errors="ignore").strip()
        except Exception:
            return ""

    # Try generic text decode for unknown non-binary files
    if not name.endswith((".pdf", ".png", ".jpg", ".jpeg", ".tif", ".tiff", ".bmp", ".gif")):
        try:
            decoded = data.decode("utf-8")
            if decoded.strip():
                return decoded.strip()
        except Exception:
            pass

    # PDF handling
    if name.endswith(".pdf"):
        if _PDFPLUMBER:
            try:
                with pdfplumber.open(io.BytesIO(data)) as pdf:
                    for page in pdf.pages:
                        page_text = page.extract_text() or ""
                        text_parts.append(page_text)
                result = "\n".join(text_parts).strip()
                if result:
                    return result
            except Exception:
                pass
        if _PYPDF and PdfReader is not None:
            try:
                reader = PdfReader(io.BytesIO(data))
                for page in reader.pages:
                    text_parts.append(page.extract_text() or "")
                result = "\n".join(text_parts).strip()
                if result:
                    return result
            except Exception:
                pass
        return ""

    # Image handling
    if Image is not None and _TESSERACT:
        try:
            img = Image.open(io.BytesIO(data))
            return pytesseract.image_to_string(img).strip()
        except Exception:
            return ""

    return ""


def ocr_available() -> bool:
    return _TESSERACT or _PDFPLUMBER or _PYPDF