from __future__ import annotations

import json
import os
import re
from typing import Optional

from .config import GROQ_API_KEY, GROQ_MODEL, GROQ_BASE_URL
from .models import InvoiceExtraction, InvoiceLine

try:
    import openai  # type: ignore

    _OPENAI = True
except Exception:  # pragma: no cover - optional dependency
    openai = None
    _OPENAI = False


SYSTEM_PROMPT = """You are an invoice data extraction engine.
Extract supplier name, invoice number, PO number, invoice date, currency, total amount,
line items (description, quantity, unit price, tax, line total) and GRN reference.
Return ONLY valid JSON with keys:
invoiceNumber, supplierName, invoiceDate, currency, totalAmount, poReference, grnReference, lines.
Use null for missing fields. lines is an array of objects with description, quantity, unitPrice, tax, lineTotal."""


def _safe_json(text: str) -> Optional[dict]:
    try:
        # strip markdown fences if present
        cleaned = text.strip()
        if cleaned.startswith("```"):
            cleaned = re.sub(r"^```(?:json)?", "", cleaned).strip()
            cleaned = re.sub(r"```$", "", cleaned).strip()
        return json.loads(cleaned)
    except Exception:
        # try to find first {...}
        m = re.search(r"\{.*\}", text, re.DOTALL)
        if m:
            try:
                return json.loads(m.group(0))
            except Exception:
                return None
        return None


def _to_extraction(data: dict, raw_text: str, source: str) -> InvoiceExtraction:
    lines = []
    for l in (data.get("lines") or []):
        lines.append(
            InvoiceLine(
                description=l.get("description") or "",
                quantity=l.get("quantity"),
                unitPrice=l.get("unitPrice"),
                tax=l.get("tax"),
                lineTotal=l.get("lineTotal"),
            )
        )
    return InvoiceExtraction(
        invoiceNumber=data.get("invoiceNumber"),
        supplierName=data.get("supplierName"),
        invoiceDate=data.get("invoiceDate"),
        currency=data.get("currency"),
        totalAmount=data.get("totalAmount"),
        poReference=data.get("poReference"),
        grnReference=data.get("grnReference"),
        lines=lines,
        rawText=raw_text,
        source=source,
    )


def heuristic_extract(text: str) -> InvoiceExtraction:
    """Regex/keyword based extraction used when no LLM is available."""
    t = text or ""
    lower = t.lower()

    def find(patterns):
        for p in patterns:
            m = re.search(p, t, re.IGNORECASE)
            if m:
                return m.group(1).strip()
        return None

    invoice_number = find(
        [r"invoice\s*(?:no|number|#)\s*[:\-]?\s*([A-Z0-9\-/]+)", r"inv[-\s]?(\d{3,})"]
    )
    supplier = find([r"supplier\s*[:\-]\s*(.+)", r"vendor\s*[:\-]\s*(.+)", r"from\s*[:\-]\s*(.+)"])
    if supplier:
        supplier = supplier.splitlines()[0].strip()[:80]
    invoice_date = find([r"date\s*[:\-]\s*([0-9]{4}-[0-9]{2}-[0-9]{2})", r"date\s*[:\-]\s*([0-9]{1,2}[\/\-][0-9]{1,2}[\/\-][0-9]{2,4})"])
    currency = find([r"currency\s*[:\-]\s*([A-Z]{3})"])
    if not currency:
        for c in ["INR", "USD", "EUR", "GBP"]:
            if c in t.upper():
                currency = c
                break
    po_reference = find([r"po\s*(?:no|number|ref)?\s*[:\-]?\s*([A-Z0-9\-/]+)"])
    grn_reference = find([r"grn\s*(?:no|number|ref)?\s*[:\-]?\s*([A-Z0-9\-/]+)"])

    total = None
    m = re.search(r"total\s*(?:amount)?\s*[:\-]?\s*[\$₹€£]?\s*([0-9][0-9,\.]*)", t, re.IGNORECASE)
    if m:
        try:
            total = float(m.group(1).replace(",", ""))
        except ValueError:
            total = None

    # simple line item parsing: lines like "desc qty price tax total"
    lines = []
    for line in t.splitlines():
        line = line.strip()
        if not line or len(line) < 6:
            continue
        # heuristic: capture description + numbers
        nums = re.findall(r"\d[\d,\.]*", line)
        if len(nums) >= 3 and not re.search(r"total|subtotal|tax", line, re.IGNORECASE):
            # take first token chunk as description
            desc = re.sub(r"\d[\d,\.]*", "", line).strip(" -:,")
            if desc:
                try:
                    qty = float(nums[0].replace(",", ""))
                    price = float(nums[1].replace(",", ""))
                    lt = float(nums[-1].replace(",", ""))
                except ValueError:
                    qty, price, lt = None, None, None
                lines.append(InvoiceLine(description=desc[:120], quantity=qty, unitPrice=price, lineTotal=lt))

    return InvoiceExtraction(
        invoiceNumber=invoice_number,
        supplierName=supplier,
        invoiceDate=invoice_date,
        currency=currency,
        totalAmount=total,
        poReference=po_reference,
        grnReference=grn_reference,
        lines=lines[:20],
        rawText=t,
        source="heuristic",
    )


class LLMExtractor:
    def __init__(self):
        self.provider = "groq"
        self.api_key = GROQ_API_KEY
        self.model = GROQ_MODEL
        self.base_url = GROQ_BASE_URL
        self.available = _OPENAI and bool(self.api_key)

    def extract(self, text: str) -> InvoiceExtraction:
        if self.available:
            try:
                client = openai.OpenAI(api_key=self.api_key, base_url=self.base_url)
                resp = client.chat.completions.create(
                    model=self.model,
                    messages=[
                        {"role": "system", "content": SYSTEM_PROMPT},
                        {"role": "user", "content": text or ""},
                    ],
                    temperature=0,
                )
                content = resp.choices[0].message.content or ""
                data = _safe_json(content)
                if data:
                    return _to_extraction(data, text, "llm:groq")
            except Exception:
                pass
        return heuristic_extract(text)