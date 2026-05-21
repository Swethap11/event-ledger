You are a senior Python developer. Generate `app/main.py` for the Event Ledger API.

## Stack
- Python 3.12, FastAPI

## Exact requirements

```python
app = FastAPI(
    title="Event Ledger API",
    description="Idempotent financial transaction ledger with out-of-order event support.",
    version="1.0.0",
)
```

## Must include
1. CORS middleware — allow localhost:3000, methods GET and POST only
2. Include events router from app.routes.events
3. Include accounts router from app.routes.accounts
4. `@app.on_event("startup")` → calls `init_db()`
5. `GET /health` → returns `{"status": "ok"}`
6. Global exception handler for unhandled exceptions:
   - Log the error using get_logger
   - Return JSONResponse with status 500 and `{"detail": "Internal server error"}`
   - Never expose stack traces in the response

## Imports needed
```python
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from app.core.database import init_db
from app.core.logging_config import get_logger
from app.routes import events, accounts
```

## Rules
- No placeholders. No TODOs. Complete file only.
- The global exception handler must catch `Exception` and return 500, logging the full traceback internally but never exposing it to the client.
