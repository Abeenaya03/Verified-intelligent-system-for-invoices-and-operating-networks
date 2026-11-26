import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from app.extraction import extract_from_text
from app.missing_data import detect_missing
from app.models import InvoiceExtraction


def test_missing_fields_detected():
    inv = InvoiceExtraction(supplierName="Acme")
    report = detect_missing(inv)
    assert report.isComplete is False
    fields = {m.field for m in report.missing}
    assert "invoiceNumber" in fields
    assert "totalAmount" in fields


def test_complete_invoice_no_missing():
    inv = InvoiceExtraction(
        supplierName="Acme",
        invoiceNumber="INV-1",
        invoiceDate="2026-10-28",
        currency="INR",
        totalAmount=100.0,
        lines=[],
    )
    # lines empty triggers missing lines, so add a line
    from app.models import InvoiceLine
    inv.lines = [InvoiceLine(description="item", quantity=1, unitPrice=100, lineTotal=100)]
    report = detect_missing(inv)
    assert report.isComplete is True


def test_extract_missing_data_flag():
    text = "Supplier: Acme\nTotal Amount: 100"
    res = extract_from_text(text, use_llm=False)
    assert res.missingData.isComplete is False