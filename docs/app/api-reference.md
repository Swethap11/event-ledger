# API Reference

Base URL: `http://localhost:8000`

---

## POST /events

Submit a financial event. Idempotent — submitting the same `eventId` twice returns the original record without creating a duplicate.

### Request

```json
{
  "eventId": "evt-001",
  "accountId": "acct-123",
  "type": "CREDIT",
  "amount": 150.00,
  "currency": "USD",
  "eventTimestamp": "2026-05-15T10:00:00Z"
}
```

| Field | Type | Required | Rules |
|---|---|---|---|
| `eventId` | string | Yes | Unique event identifier |
| `accountId` | string | Yes | Account this event belongs to |
| `type` | string | Yes | `"CREDIT"` or `"DEBIT"` |
| `amount` | number | Yes | Must be > 0 |
| `currency` | string | Yes | ISO 4217 code e.g. `"USD"` |
| `eventTimestamp` | string | Yes | ISO 8601 e.g. `"2026-05-15T10:00:00Z"` |

### Responses

| Status | Meaning |
|---|---|
| `201 Created` | New event accepted and stored |
| `200 OK` | Duplicate `eventId` — original event returned, nothing stored |
| `422 Unprocessable Entity` | Validation failed (invalid type, amount ≤ 0, etc.) |

### Example

```bash
curl -X POST http://localhost:8000/events \
  -H "Content-Type: application/json" \
  -d '{
    "eventId": "evt-001",
    "accountId": "acct-123",
    "type": "CREDIT",
    "amount": 150.00,
    "currency": "USD",
    "eventTimestamp": "2026-05-15T10:00:00Z"
  }'
```

```json
{
  "eventId": "evt-001",
  "accountId": "acct-123",
  "type": "CREDIT",
  "amount": "150.00000000",
  "currency": "USD",
  "eventTimestamp": "2026-05-15T10:00:00Z",
  "createdAt": "2026-05-21T09:00:00Z"
}
```

---

## GET /events/{eventId}

Retrieve a single event by its ID.

### Responses

| Status | Meaning |
|---|---|
| `200 OK` | Event found — returns event object |
| `404 Not Found` | No event with this ID |

### Example

```bash
curl http://localhost:8000/events/evt-001
```

---

## GET /events?account={accountId}

List all events for an account, ordered by `eventTimestamp` ascending (not arrival order).

This ordering is what makes the ledger out-of-order safe — a late-arriving event with an earlier timestamp will be inserted in the correct chronological position.

### Query Parameters

| Parameter | Required | Description |
|---|---|---|
| `account` | Yes | Account ID to filter by |

### Responses

| Status | Meaning |
|---|---|
| `200 OK` | Array of events (empty array if account has no events) |

### Example

```bash
curl "http://localhost:8000/events?account=acct-123"
```

```json
[
  {
    "eventId": "evt-001",
    "accountId": "acct-123",
    "type": "CREDIT",
    "amount": "150.00000000",
    "currency": "USD",
    "eventTimestamp": "2026-05-15T10:00:00Z"
  },
  {
    "eventId": "evt-002",
    "accountId": "acct-123",
    "type": "DEBIT",
    "amount": "50.00000000",
    "currency": "USD",
    "eventTimestamp": "2026-05-16T14:00:00Z"
  }
]
```

---

## GET /accounts/{accountId}/balance

Get the current net balance for an account.

Balance = sum of all CREDITs − sum of all DEBITs, computed from the full event log ordered by `eventTimestamp`. Out-of-order events are handled correctly — a late-arriving event will shift the balance as if it had arrived at its timestamp.

### Responses

| Status | Meaning |
|---|---|
| `200 OK` | Balance object returned |
| `404 Not Found` | No events found for this account |

### Example

```bash
curl http://localhost:8000/accounts/acct-123/balance
```

```json
{
  "accountId": "acct-123",
  "balance": "100.00000000",
  "currency": "USD"
}
```

> **Note:** `balance` is returned as a string with 8 decimal places (Decimal precision). Parse with `Decimal(response["balance"])` or `float(response["balance"])` depending on your needs.

---

## GET /health

Health check — confirms the server is running.

```bash
curl http://localhost:8000/health
```

```json
{ "status": "ok" }
```

---

## Error Responses

All errors return structured JSON — never a raw stack trace.

```json
{ "detail": "Event not found" }
```

Validation errors (422) include field-level detail from Pydantic:

```json
{
  "detail": [
    {
      "loc": ["body", "amount"],
      "msg": "Input should be greater than 0",
      "type": "greater_than"
    }
  ]
}
```

---

## Idempotency Behaviour

Submitting the same `eventId` twice is safe and expected:

| Attempt | Status | Effect |
|---|---|---|
| First submission | `201 Created` | Event stored |
| Any repeat | `200 OK` | Original event returned, nothing written |

The response body is identical in both cases — the status code is the only difference. This means clients can safely retry on network failure without risk of double-counting.
