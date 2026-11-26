import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

os.environ["AUDIT_DB_PATH"] = os.path.join(os.path.dirname(__file__), "test_dup.db")

from fastapi.testclient import TestClient
from app.main import app
from app import db

client = TestClient(app)


def setup_function():
    if os.path.exists(os.environ["AUDIT_DB_PATH"]):
        os.remove(os.environ["AUDIT_DB_PATH"])
    db.init_db()


def test_duplicate_flow():
    req = {"supplierName": "Acme", "invoiceNumber": "INV-1", "invoiceDate": "2026-10-28", "currency": "INR", "totalAmount": 100.0}
    r = client.post("/duplicate/check", json=req)
    assert r.status_code == 200
    assert r.json()["isDuplicate"] is False
    # register
    rreg = client.post("/duplicate/register", json=req, params={"invoice_id": "inv-1"})
    assert rreg.status_code == 200
    # check again
    r2 = client.post("/duplicate/check", json=req)
    assert r2.json()["isDuplicate"] is True
    assert r2.json()["matchedId"] == "inv-1"


def test_report_summary():
    r = client.get("/reports/summary")
    assert r.status_code == 200
    assert "totalEvents" in r.json()