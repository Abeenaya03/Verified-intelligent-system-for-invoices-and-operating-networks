import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

# isolate db
os.environ["AUDIT_DB_PATH"] = os.path.join(os.path.dirname(__file__), "test_audit.db")

from fastapi.testclient import TestClient
from app.main import app
from app import db

client = TestClient(app)


def setup_function():
    # clean db
    if os.path.exists(os.environ["AUDIT_DB_PATH"]):
        os.remove(os.environ["AUDIT_DB_PATH"])
    db.init_db()


def test_health():
    r = client.get("/health")
    assert r.status_code == 200


def test_create_and_list_event():
    payload = {"actor": "reviewer", "action": "STATUS_CHANGED", "invoiceId": "inv-1", "oldStatus": "A", "newStatus": "B"}
    r = client.post("/audit/events", json=payload)
    assert r.status_code == 200
    eid = r.json()["id"]
    r2 = client.get("/audit/events", params={"invoiceId": "inv-1"})
    assert r2.status_code == 200
    assert any(e["id"] == eid for e in r2.json())


def test_get_event_404():
    r = client.get("/audit/events/nonexistent")
    assert r.status_code == 404