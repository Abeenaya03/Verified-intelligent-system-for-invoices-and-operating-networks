from __future__ import annotations

from typing import Optional

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware

from .db import (
    check_duplicate,
    create_audit_event,
    get_audit_event,
    init_db,
    list_audit_events,
    register_duplicate,
    report_summary,
)
from .models import AuditEvent, DuplicateCheckRequest, DuplicateCheckResponse, ReportSummary

app = FastAPI(title="V.I.S.I.O.N Member 4 - Audit & Duplicate Detection", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

init_db()


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/audit/events")
def create_event(event: AuditEvent):
    return create_audit_event(event.model_dump())


@app.get("/audit/events")
def list_events(
    invoiceId: Optional[str] = Query(None),
    actor: Optional[str] = Query(None),
    action: Optional[str] = Query(None),
    limit: int = Query(100, ge=1, le=500),
):
    return list_audit_events(invoice_id=invoiceId, actor=actor, action=action, limit=limit)


@app.get("/audit/events/{event_id}")
def get_event(event_id: str):
    ev = get_audit_event(event_id)
    if not ev:
        raise HTTPException(status_code=404, detail="Event not found")
    return ev


@app.post("/duplicate/check", response_model=DuplicateCheckResponse)
def duplicate_check(req: DuplicateCheckRequest):
    return check_duplicate(req.model_dump())


@app.post("/duplicate/register")
def duplicate_register(req: DuplicateCheckRequest, invoice_id: Optional[str] = None):
    new_id = register_duplicate(req.model_dump(), invoice_id)
    return {"registered": True, "invoice_id": new_id}


@app.get("/reports/summary", response_model=ReportSummary)
def summary():
    return report_summary()