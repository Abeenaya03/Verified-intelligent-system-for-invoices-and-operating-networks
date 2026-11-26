import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_health():
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"


def test_extract_text_endpoint():
    payload = {"text": "Supplier: Acme\nInvoice Number: INV-1\nInvoice Date: 2026-10-28\nCurrency: INR\nTotal Amount: 100", "use_llm": False}
    r = client.post("/extract-text", json=payload)
    assert r.status_code == 200
    data = r.json()
    assert data["invoice"]["invoiceNumber"] == "INV-1"