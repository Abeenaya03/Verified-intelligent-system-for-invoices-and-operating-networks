from __future__ import annotations

from .models import InvoiceExtraction, MissingDataReport, MissingField

REQUIRED_FIELDS = ["supplierName", "invoiceNumber", "invoiceDate", "currency", "totalAmount"]


def detect_missing(invoice: InvoiceExtraction) -> MissingDataReport:
    missing: list[MissingField] = []
    for field in REQUIRED_FIELDS:
        value = getattr(invoice, field, None)
        if value is None or (isinstance(value, str) and not value.strip()):
            missing.append(MissingField(field=field, reason="Field is missing or unreadable."))
    if not invoice.lines:
        missing.append(MissingField(field="lines", reason="No line items extracted."))
    return MissingDataReport(missing=missing, isComplete=len(missing) == 0)