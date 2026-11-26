from __future__ import annotations

from typing import Optional
from pydantic import BaseModel, Field


class AuditEvent(BaseModel):
    id: Optional[str] = None
    actor: str
    action: str
    timestamp: Optional[str] = None
    invoiceId: Optional[str] = None
    oldStatus: Optional[str] = None
    newStatus: Optional[str] = None
    reason: Optional[str] = None
    comment: Optional[str] = None


class DuplicateCheckRequest(BaseModel):
    invoiceNumber: Optional[str] = None
    supplierName: Optional[str] = None
    invoiceDate: Optional[str] = None
    currency: Optional[str] = None
    totalAmount: Optional[float] = None
    fingerprint: Optional[str] = None  # optional precomputed


class DuplicateCheckResponse(BaseModel):
    isDuplicate: bool = False
    matchedId: Optional[str] = None
    similarity: float = 0.0
    reason: str = ""


class ReportSummary(BaseModel):
    totalEvents: int = 0
    eventsByAction: dict[str, int] = Field(default_factory=dict)
    duplicateChecks: int = 0
    duplicatesFound: int = 0