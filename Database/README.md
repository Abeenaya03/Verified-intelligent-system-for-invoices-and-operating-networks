# Member 4 - Audit History & Duplicate Detection Service

## Run
```bash
cd member4
python -m uvicorn app.main:app --reload --port 8002
```

## Test
```bash
cd member4
python -m pytest -q
```

## Endpoints
- `GET /health`
- `POST /audit/events`
- `GET /audit/events` (filters: invoiceId, actor, action)
- `GET /audit/events/{id}`
- `POST /duplicate/check`
- `POST /duplicate/register`
- `GET /reports/summary`