from __future__ import annotations

import hashlib
import json
import os
import sqlite3
import uuid
from datetime import datetime, timezone
from typing import Any, Optional

DB_PATH = os.getenv("AUDIT_DB_PATH", os.path.join(os.path.dirname(__file__), "..", "audit.db"))
DB_PATH = os.path.abspath(DB_PATH)


def _connect() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    conn = _connect()
    try:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS audit_events (
                id TEXT PRIMARY KEY,
                actor TEXT NOT NULL,
                action TEXT NOT NULL,
                timestamp TEXT NOT NULL,
                invoice_id TEXT,
                old_status TEXT,
                new_status TEXT,
                reason TEXT,
                comment TEXT
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS duplicate_registry (
                fingerprint TEXT PRIMARY KEY,
                invoice_id TEXT NOT NULL,
                supplier_name TEXT,
                invoice_number TEXT,
                invoice_date TEXT,
                currency TEXT,
                total_amount REAL,
                created_at TEXT NOT NULL
            )
            """
        )
        conn.commit()
    finally:
        conn.close()


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def create_audit_event(event: dict[str, Any]) -> dict[str, Any]:
    init_db()
    eid = event.get("id") or str(uuid.uuid4())
    record = {
        "id": eid,
        "actor": event["actor"],
        "action": event["action"],
        "timestamp": event.get("timestamp") or _now(),
        "invoice_id": event.get("invoiceId"),
        "old_status": event.get("oldStatus"),
        "new_status": event.get("newStatus"),
        "reason": event.get("reason"),
        "comment": event.get("comment"),
    }
    conn = _connect()
    try:
        conn.execute(
            """INSERT INTO audit_events
               (id, actor, action, timestamp, invoice_id, old_status, new_status, reason, comment)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                record["id"],
                record["actor"],
                record["action"],
                record["timestamp"],
                record["invoice_id"],
                record["old_status"],
                record["new_status"],
                record["reason"],
                record["comment"],
            ),
        )
        conn.commit()
    finally:
        conn.close()
    return {
        "id": record["id"],
        "actor": record["actor"],
        "action": record["action"],
        "timestamp": record["timestamp"],
        "invoiceId": record["invoice_id"],
        "oldStatus": record["old_status"],
        "newStatus": record["new_status"],
        "reason": record["reason"],
        "comment": record["comment"],
    }


def list_audit_events(
    invoice_id: Optional[str] = None,
    actor: Optional[str] = None,
    action: Optional[str] = None,
    limit: int = 100,
) -> list[dict[str, Any]]:
    init_db()
    query = "SELECT * FROM audit_events WHERE 1=1"
    params: list[Any] = []
    if invoice_id:
        query += " AND invoice_id = ?"
        params.append(invoice_id)
    if actor:
        query += " AND actor = ?"
        params.append(actor)
    if action:
        query += " AND action = ?"
        params.append(action)
    query += " ORDER BY timestamp DESC LIMIT ?"
    params.append(limit)
    conn = _connect()
    try:
        rows = conn.execute(query, params).fetchall()
    finally:
        conn.close()
    return [
        {
            "id": r["id"],
            "actor": r["actor"],
            "action": r["action"],
            "timestamp": r["timestamp"],
            "invoiceId": r["invoice_id"],
            "oldStatus": r["old_status"],
            "newStatus": r["new_status"],
            "reason": r["reason"],
            "comment": r["comment"],
        }
        for r in rows
    ]


def get_audit_event(eid: str) -> Optional[dict[str, Any]]:
    init_db()
    conn = _connect()
    try:
        r = conn.execute("SELECT * FROM audit_events WHERE id = ?", (eid,)).fetchone()
    finally:
        conn.close()
    if not r:
        return None
    return {
        "id": r["id"],
        "actor": r["actor"],
        "action": r["action"],
        "timestamp": r["timestamp"],
        "invoiceId": r["invoice_id"],
        "oldStatus": r["old_status"],
        "newStatus": r["new_status"],
        "reason": r["reason"],
        "comment": r["comment"],
    }


def _fingerprint(req: dict[str, Any]) -> str:
    if req.get("fingerprint"):
        return req["fingerprint"]
    parts = [
        (req.get("supplierName") or "").strip().lower(),
        (req.get("invoiceNumber") or "").strip().lower(),
        (req.get("invoiceDate") or "").strip().lower(),
        str(req.get("totalAmount")),
        (req.get("currency") or "").strip().upper(),
    ]
    raw = "|".join(parts)
    return hashlib.sha256(raw.encode()).hexdigest()


def check_duplicate(req: dict[str, Any]) -> dict[str, Any]:
    init_db()
    fp = _fingerprint(req)
    conn = _connect()
    try:
        row = conn.execute("SELECT * FROM duplicate_registry WHERE fingerprint = ?", (fp,)).fetchone()
    finally:
        conn.close()
    if row:
        # similarity = field overlap
        sim = 1.0
        return {
            "isDuplicate": True,
            "matchedId": row["invoice_id"],
            "similarity": sim,
            "reason": "Exact fingerprint match (supplier+number+date+total+currency).",
        }
    # fuzzy: check by invoice number + supplier
    conn = _connect()
    try:
        rows = conn.execute(
            "SELECT * FROM duplicate_registry WHERE invoice_number = ? OR supplier_name = ?",
            (req.get("invoiceNumber"), req.get("supplierName")),
        ).fetchall()
    finally:
        conn.close()
    best_sim = 0.0
    best_id = None
    for r in rows:
        score = 0.0
        total = 0
        pairs = [
            (req.get("supplierName"), r["supplier_name"]),
            (req.get("invoiceNumber"), r["invoice_number"]),
            (req.get("invoiceDate"), r["invoice_date"]),
            (req.get("totalAmount"), r["total_amount"]),
            (req.get("currency"), r["currency"]),
        ]
        for x, y in pairs:
            total += 1
            if x is not None and x == y:
                score += 1
        sim = (score / total) if total else 0.0
        if sim > best_sim:
            best_sim = sim
            best_id = r["invoice_id"]
    if best_sim >= 0.6 and best_id:
        return {
            "isDuplicate": True,
            "matchedId": best_id,
            "similarity": round(best_sim, 2),
            "reason": "High field similarity with an existing invoice.",
        }
    return {"isDuplicate": False, "matchedId": None, "similarity": 0.0, "reason": "No duplicate found."}


def register_duplicate(req: dict[str, Any], invoice_id: Optional[str] = None) -> str:
    init_db()
    fp = _fingerprint(req)
    new_id = invoice_id or fp[:12]
    conn = _connect()
    try:
        conn.execute(
            """INSERT OR REPLACE INTO duplicate_registry
               (fingerprint, invoice_id, supplier_name, invoice_number, invoice_date, currency, total_amount, created_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                fp,
                new_id,
                req.get("supplierName"),
                req.get("invoiceNumber"),
                req.get("invoiceDate"),
                req.get("currency"),
                req.get("totalAmount"),
                _now(),
            ),
        )
        conn.commit()
    finally:
        conn.close()
    return new_id


def report_summary() -> dict[str, Any]:
    init_db()
    conn = _connect()
    try:
        total_events = conn.execute("SELECT COUNT(*) AS c FROM audit_events").fetchone()["c"]
        rows = conn.execute("SELECT action, COUNT(*) AS c FROM audit_events GROUP BY action").fetchall()
        dup_checks = 0  # not tracked separately; approximate via registry size
        registry_size = conn.execute("SELECT COUNT(*) AS c FROM duplicate_registry").fetchone()["c"]
    finally:
        conn.close()
    return {
        "totalEvents": total_events,
        "eventsByAction": {r["action"]: r["c"] for r in rows},
        "duplicateChecks": registry_size,
        "duplicatesFound": 0,
    }