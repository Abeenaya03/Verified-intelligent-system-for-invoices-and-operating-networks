from __future__ import annotations

from typing import Any, Optional
from pydantic import BaseModel, Field


class InvoiceLine(BaseModel):
    description: str
    quantity: Optional[float] = None
    unitPrice: Optional[float] = None
    tax: Optional[float] = None
    lineTotal: Optional[float] = None


class InvoiceExtraction(BaseModel):
    invoiceNumber: Optional[str] = None
    supplierName: Optional[str] = None
    invoiceDate: Optional[str] = None
    currency: Optional[str] = None
    totalAmount: Optional[float] = None
    poReference: Optional[str] = None
    grnReference: Optional[str] = None
    lines: list[InvoiceLine] = Field(default_factory=list)
    rawText: Optional[str] = None
    source: str = "heuristic"  # "llm" | "heuristic" | "ocr+llm"


class MissingField(BaseModel):
    field: str
    reason: str


class MissingDataReport(BaseModel):
    missing: list[MissingField] = Field(default_factory=list)
    isComplete: bool = True


class DuplicateResult(BaseModel):
    isDuplicate: bool = False
    matchedId: Optional[str] = None
    similarity: float = 0.0
    reason: str = ""


class ExtractionResult(BaseModel):
    invoice: InvoiceExtraction
    missingData: MissingDataReport
    duplicate: Optional[DuplicateResult] = None
    metadata: dict[str, Any] = Field(default_factory=dict)