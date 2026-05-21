You are a senior Python developer. Generate the `app/repositories/` module for the Event Ledger API.

## Stack
- Python 3.12, SQLModel, SQLite

## Files to generate
1. `app/repositories/__init__.py` — empty
2. `app/repositories/event_repo.py` — all database access

## Exact class: EventRepository

```python
class EventRepository:
    def __init__(self, session: Session): ...

    def get_by_id(self, event_id: str) -> Event | None: ...
    # Uses: session.get(Event, event_id)

    def get_by_account(self, account_id: str) -> list[Event]: ...
    # ORDER BY event_timestamp ASC — always chronological regardless of arrival order

    def create(self, payload: EventCreate) -> Event: ...
    # Serialises metadata dict to JSON string
    # Sets received_at = datetime.utcnow()

    def get_balance(self, account_id: str) -> tuple[Decimal, str | None]: ...
    # Returns (balance, currency)
    # Use func.sum() via SQLModel select — MUST use Decimal, NOT float
    # balance = Decimal(credit_sum) - Decimal(debit_sum)

    def account_exists(self, account_id: str) -> bool: ...
    # SELECT ... LIMIT 1

    def write_audit(self, endpoint: str, status_code: int, outcome: str,
                    event_id: str | None, account_id: str | None, ip: str | None) -> None: ...
    # Writes one AuditLog row — called after every API operation
```

## Rules
- Use SQLModel `select()` for all queries — never raw SQL strings.
- Idempotency is enforced by `event_id` being the primary key. Do NOT do application-level "check if exists before insert". Let the DB raise on duplicate and catch it in the service layer.
- Import `Decimal` from `decimal` and use it for all amount/balance types.
- EventCreate fields are camelCase: use `payload.eventId`, `payload.accountId`, `payload.eventTimestamp`.
- AuditLog IP field is `ip_address`, not `ip`.
- No placeholders. No TODOs. Complete file only.
- Import Event, AuditLog from app.models.orm and EventCreate from app.models.schemas.
- Keep every line at or below 88 characters (Ruff E501).
