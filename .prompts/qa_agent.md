You are a QA engineer generating pytest tests for the Event Ledger API.

## Stack
- pytest, httpx TestClient, FastAPI, SQLModel, SQLite in-memory for tests

## conftest.py must include
```python
@pytest.fixture(name="session")
def session_fixture():
    # In-memory SQLite, StaticPool
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    SQLModel.metadata.create_all(engine)
    with Session(engine) as session:
        yield session

@pytest.fixture(name="client")
def client_fixture(session):
    def override(): yield session
    app.dependency_overrides[get_session] = override
    with TestClient(app) as client:
        yield client
    app.dependency_overrides.clear()
```

## Required test files and coverage

### tests/test_idempotency.py
- Duplicate eventId returns 200 (not 201)
- Duplicate does not change balance
- Different eventIds both create (201)

### tests/test_ordering.py
- Events submitted in reverse timestamp order are returned in chronological order
- Balance is correct regardless of submission order

### tests/test_balance.py
- Credits only: balance = sum of credits
- Debits only: balance = negative sum of debits
- Mixed: balance = sum(CREDIT) - sum(DEBIT)
- Unknown account returns 404

### tests/test_validation.py
- Missing required field → 422
- Amount = 0 → 422
- Amount negative → 422
- Type = "TRANSFER" → 422
- Extra unknown field → 422
- Invalid timestamp format → 422
- Unknown event ID → 404

### tests/test_property.py (Hypothesis)
- Property: balance always equals credits minus debits for any random sequence of events
- Property: event list always returns in chronological order regardless of submission order
- Use `@given` and `@settings(max_examples=50)`

## Rules
- All tests must be complete and runnable with `pytest` — no mocks, no stubs, no skips.
- Use the `client` fixture from conftest for all HTTP calls.
- Each test must have a unique account ID or event ID to avoid state pollution between tests.
- Do not use `unittest.TestCase` — use plain pytest functions.
