import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from app.extraction import extract_from_text
from app.llm import heuristic_extract


SAMPLE_INVOICE = """
Supplier: Acme Technologies
Invoice Number: INV-2026-001
Invoice Date: 2026-10-28
Currency: INR
PO Number: PO-4412
Total Amount: 1125000
Cloud hosting (annual) 1 900000 162000 1062000
Support plan 1 50000 9000 59000
"""


def test_heuristic_extracts_core_fields():
    inv = heuristic_extract(SAMPLE_INVOICE)
    assert inv.invoiceNumber == "INV-2026-001"
    assert inv.supplierName is not None and "Acme" in inv.supplierName
    assert inv.invoiceDate == "2026-10-28"
    assert inv.currency == "INR"
    assert inv.totalAmount == 1125000.0
    assert inv.poReference == "PO-4412"


def test_extract_from_text_returns_result():
    res = extract_from_text(SAMPLE_INVOICE, use_llm=False)
    assert res.invoice.invoiceNumber == "INV-2026-001"
    assert res.missingData.isComplete is True
    assert res.duplicate is not None


def test_structured_json_serializable():
    res = extract_from_text(SAMPLE_INVOICE, use_llm=False)
    data = res.model_dump()
    assert "invoice" in data
    assert isinstance(data["invoice"]["lines"], list)