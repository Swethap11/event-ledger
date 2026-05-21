You are a senior Python developer. Generate the `app/models/` module for the Event Ledger API.

## Stack
- Python 3.12, FastAPI, SQLModel, SQLite, Pydantic v2

## Files to generate
1. `app/models/__init__.py` — empty
2. `app/models/orm.py` — SQLModel ORM table definitions
3. `app/models/schemas.py` — Pydantic v2 request/response schemas

## Exact requirements for orm.py

Two tables:

### Event table
```python
class Event(SQLModel, table=True):
    __tablename__ = "events"
    event_id: str = Field(primary_key=True)
    account_id: str = Field(index=True, nullable=False)
    type: str = Field(nullable=False)          # "CREDIT" or "DEBIT"
    amount: Decimal = Field(                   # MUST be Decimal, not float
        sa_column=Column(Numeric(precision=18, scale=8), nullable=False)
    )
    currency: str = Field(nullable=False)
    event_timestamp: datetime = Field(sa_column=Column(DateTime(timezone=True), nullable=False, index=True))
    metadata_json: str | None = Field(default=None)   # JSON serialised dict
    received_at: datetime = Field(default_factory=datetime.utcnow)
```

### AuditLog table
```python
class AuditLog(SQLModel, table=True):
    __tablename__ = "audit_log"
    id: int | None = Field(default=None, primary_key=True)
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    endpoint: str          # e.g. "POST /events"
    event_id: str | None = Field(default=None)
    account_id: str | None = Field(default=None)
    status_code: int
    outcome: str           # "CREATED", "DUPLICATE", "REJECTED", "ERROR", "FETCHED"
    ip_address: str | None = Field(default=None)
```

## Exact requirements for schemas.py

```python
class EventType(str, Enum):
    CREDIT = "CREDIT"
    DEBIT = "DEBIT"

class EventCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    eventId: str
    accountId: str
    type: EventType
    amount: Annotated[Decimal, Field(gt=0, description="Must be greater than 0")]
    currency: str
    eventTimestamp: datetime
    metadata: dict[str, Any] | None = None

class EventResponse(BaseModel):
    eventId: str
    accountId: str
    type: EventType
    amount: Decimal
    currency: str
    eventTimestamp: datetime
    metadata: dict[str, Any] | None = None
    receivedAt: datetime

class BalanceResponse(BaseModel):
    accountId: str
    balance: Decimal
    currency: str

class ErrorResponse(BaseModel):
    detail: str
```

## Rules
- Import `Column`, `DateTime`, `Numeric` from `sqlalchemy` for ORM fields.
- Import `Decimal` from `decimal` for all amount/balance fields.
- Use `from typing import Annotated, Any` — do NOT use `pydantic.typing`.
- No placeholders. No TODOs. Complete files only.
- All imports must resolve with sqlmodel, pydantic, sqlalchemy installed.
- Keep every line at or below 88 characters (Ruff E501).
