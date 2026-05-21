You are a senior Python developer. Generate the `app/routes/` module for the Event Ledger API.

## Stack
- Python 3.12, FastAPI, Pydantic v2

## Files to generate
1. `app/routes/__init__.py` — empty
2. `app/routes/events.py` — events router
3. `app/routes/accounts.py` — accounts router

## Exact endpoints

### app/routes/events.py
```python
router = APIRouter(prefix="/events", tags=["Events"])

@router.post("", status_code=201, response_model=EventResponse)
def submit_event(payload: EventCreate, request: Request, session: Session = Depends(get_session)):
    # Call EventService.submit()
    # If duplicate (created=False): return JSONResponse with status_code=200
    # If new (created=True): return response with status_code=201

@router.get("/{event_id}", response_model=EventResponse)
def get_event(event_id: str, session: Session = Depends(get_session)):
    # Call EventService.get_by_id()
    # Catch EventNotFoundError → return JSONResponse 404 with {"detail": "Event '...' not found"}

@router.get("", response_model=list[EventResponse])
def list_events(account: str = Query(..., description="Account ID"), session: Session = Depends(get_session)):
    # Call EventService.list_by_account()
    # Always returns list (empty list is valid)
```

### app/routes/accounts.py
```python
router = APIRouter(prefix="/accounts", tags=["Accounts"])

@router.get("/{account_id}/balance", response_model=BalanceResponse)
def get_balance(account_id: str, session: Session = Depends(get_session)):
    # Call EventService.get_balance()
    # Catch AccountNotFoundError → return JSONResponse 404 with {"detail": "Account '...' not found"}
```

## Rules
- Import get_session from app.core.database
- Import EventService from app.services.event_service
- Import EventNotFoundError, AccountNotFoundError from app.core.exceptions
- Import EventCreate, EventResponse, BalanceResponse from app.models.schemas
- No stack traces in error responses — always {"detail": "..."} JSON only
- No placeholders. No TODOs. Complete files only.
