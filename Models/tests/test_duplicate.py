import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from app.duplicate import DuplicateDetector
from app.models import InvoiceExtraction


def test_duplicate_detection():
    det = DuplicateDetector()
    inv1 = InvoiceExtraction(supplierName="Acme", invoiceNumber="INV-1", invoiceDate="2026-10-28", currency="INR", totalAmount=100.0)
    r1 = det.check(inv1)
    assert r1.isDuplicate is False
    det.register(inv1, "inv-1")
    inv2 = InvoiceExtraction(supplierName="Acme", invoiceNumber="INV-1", invoiceDate="2026-10-28", currency="INR", totalAmount=100.0)
    r2 = det.check(inv2)
    assert r2.isDuplicate is True
    assert r2.matchedId == "inv-1"