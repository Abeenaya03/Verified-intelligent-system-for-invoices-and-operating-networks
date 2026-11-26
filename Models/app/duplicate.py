from __future__ import annotations

import hashlib
from typing import Optional

from .models import InvoiceExtraction, DuplicateResult


class DuplicateDetector:
    def __init__(self):
        self._registry: dict[str, str] = {}  # fingerprint -> invoice id

    def _fingerprint(self, invoice: InvoiceExtraction) -> str:
        parts = [
            (invoice.supplierName or "").strip().lower(),
            (invoice.invoiceNumber or "").strip().lower(),
            (invoice.invoiceDate or "").strip().lower(),
            str(invoice.totalAmount),
            (invoice.currency or "").strip().upper(),
        ]
        raw = "|".join(parts)
        return hashlib.sha256(raw.encode()).hexdigest()

    def _similarity(self, a: InvoiceExtraction, b_invoice_id: Optional[str], registry_inv: Optional[InvoiceExtraction]) -> float:
        # Simple field-overlap similarity
        if registry_inv is None:
            return 1.0 if True else 0.0
        score = 0.0
        total = 0
        pairs = [
            (a.supplierName, registry_inv.supplierName),
            (a.invoiceNumber, registry_inv.invoiceNumber),
            (a.invoiceDate, registry_inv.invoiceDate),
            (a.totalAmount, registry_inv.totalAmount),
            (a.currency, registry_inv.currency),
        ]
        for x, y in pairs:
            total += 1
            if x is not None and x == y:
                score += 1
        return score / total if total else 0.0

    def check(self, invoice: InvoiceExtraction, candidate_id: Optional[str] = None) -> DuplicateResult:
        fp = self._fingerprint(invoice)
        # exact fingerprint match
        if fp in self._registry:
            return DuplicateResult(
                isDuplicate=True,
                matchedId=self._registry[fp],
                similarity=1.0,
                reason="Exact fingerprint match (supplier+number+date+total+currency).",
            )
        # fuzzy: compare against stored by invoice number + supplier
        for stored_fp, stored_id in self._registry.items():
            pass
        # store
        new_id = candidate_id or fp[:12]
        self._registry[fp] = new_id
        return DuplicateResult(isDuplicate=False, matchedId=None, similarity=0.0, reason="No duplicate found.")

    def register(self, invoice: InvoiceExtraction, invoice_id: str) -> None:
        fp = self._fingerprint(invoice)
        self._registry[fp] = invoice_id