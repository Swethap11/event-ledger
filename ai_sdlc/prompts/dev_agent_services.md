You are a senior Python developer. Generate the `app/services/` module for the Event Ledger API.

## Stack
- Python 3.12, FastAPI, SQLModel, Pydantic v2

## Files to generate
1. `app/services/__init__.py` — empty
2. `app/services/event_service.py` — all business logic

## Exact class: EventService

```python
class EventService:
    def __init__(self, session: Session):
        self.repo = EventRepository(session)

    def submit(self, payload: EventCreate, ip: str | None = None) -> tuple[EventResponse, bool]:
        # bool = True if newly created, False if duplicate
        # Idempotency: try to create, catch duplicate primary key exception
        # Write audit log: outcome "CREATED" or "DUPLICATE"
        ...

    def get_by_id(self, event_id: str, ip: str | None = None) -> EventResponse:
        # Raises EventNotFoundError if not found
        # Write audit log: outcome "FETCHED" or "ERROR"
        ...

    def list_by_account(self, account_id: str) -> list[EventResponse]:
        # Returns events ordered by event_timestamp ASC
        # Returns empty list if account has no events (not an error)
        ...

    def get_balance(self, account_id: str) -> BalanceResponse:
        # Raises AccountNotFoundError if account has no events
        # Write audit log: outcome "FETCHED" or "ERROR"
        ...
```

## Helper function
```python
def _orm_to_response(event: Event) -> EventResponse:
    # Converts Event ORM to EventResponse
    # Deserialises metadata_json string back to dict | None
    ...
```

## Idempotency implementation
```python
from sqlalchemy.exc import IntegrityError

try:
    event = self.repo.create(payload)
    return _orm_to_response(event), True
except IntegrityError:
    session.rollback()
    existing = self.repo.get_by_id(payload.eventId)
    return _orm_to_response(existing), False
```

## Rules
- Import EventRepository from app.repositories.event_repo
- Import EventNotFoundError, AccountNotFoundError from app.core.exceptions
- No placeholders. No TODOs. Complete file only.
