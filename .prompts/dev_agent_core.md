You are a senior Python developer. Generate the `app/core/` module for the Event Ledger API.

## Stack
- Python 3.12, FastAPI, SQLModel, SQLite, Pydantic v2, uv

## Files to generate
Return exactly these files:
1. `app/__init__.py` — empty
2. `app/core/__init__.py` — empty
3. `app/core/database.py` — SQLite engine, session factory, init_db()
4. `app/core/logging_config.py` — structured JSON logger setup
5. `app/core/exceptions.py` — EventNotFoundError, AccountNotFoundError

## Exact requirements for database.py
```python
from sqlmodel import SQLModel, create_engine, Session

DATABASE_URL = "sqlite:///./ledger.db"
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})

def init_db() -> None:
    SQLModel.metadata.create_all(engine)

def get_session():  # FastAPI dependency
    with Session(engine) as session:
        yield session
```

## Exact requirements for logging_config.py
- Use Python standard `logging` module only — no third-party logging libraries
- Configure a JSON formatter that outputs: timestamp, level, logger name, message, and any extra fields
- Expose a `get_logger(name: str) -> logging.Logger` function
- Log level controlled by `LOG_LEVEL` env var, defaulting to `INFO`

## Exact requirements for exceptions.py
```python
class EventNotFoundError(Exception):
    def __init__(self, event_id: str):
        self.event_id = event_id

class AccountNotFoundError(Exception):
    def __init__(self, account_id: str):
        self.account_id = account_id
```

## Rules
- No placeholders. No TODOs. No `pass` in non-empty classes.
- All imports must be resolvable with: fastapi, sqlmodel, pydantic already installed.
- Files must be complete and runnable as-is.
- Generate a conventional commit message for this module.
