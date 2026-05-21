# Architecture

## System Overview

The complete solution has three distinct layers. The agents build the app — the app serves the API — CI runs the agents automatically on every push.

```
┌─────────────────────────────────────────────────────────────────┐
│                    AGENT PIPELINE (SDLC layer)                  │
│                                                                 │
│  .prompts/ (versioned prompt files)                             │
│       │                                                         │
│       ▼                                                         │
│  Design Agent ──► Dev Agent ──► Security Agent                  │
│                      │              │                           │
│                  Validators         │                           │
│                  (syntax, lint,     │                           │
│                  import, server,    │                           │
│                  contract, tests)   │                           │
│                      │              │                           │
│                 Self-healing     QA Agent ──► Docs Agent        │
│                 loop (3 retries)    │            │              │
│                                     │       Changelog Agent     │
│                              LangSmith trace URL                │
└─────────────────────────────────────────────────────────────────┘
                              │ generates
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                    EVENT LEDGER API (application layer)         │
│                                                                 │
│   POST /events          GET /events/{id}                        │
│   GET /events?account=  GET /accounts/{id}/balance              │
│   GET /audit-log        GET /health                             │
│                                                                 │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │  Routes  →  Services  →  Repositories                    │   │
│  │                 │                                        │   │
│  │          Structured logging (JSON)                       │   │
│  │          Global exception handler                        │   │
│  └──────────────────────────┬───────────────────────────────┘   │
│                             │                                   │
│                    ┌────────▼────────┐                          │
│                    │ SQLite database │                          │
│                    │                 │                          │
│                    │  events table   │  ← immutable event log   │
│                    │  audit_log table│  ← every API call logged │
│                    └─────────────────┘                          │
└─────────────────────────────────────────────────────────────────┘
                              │
┌─────────────────────────────────────────────────────────────────┐
│                    CI/CD (GitHub Actions)                       │
│                                                                 │
│   on: push                                                      │
│   ├── tests.yml    → pytest + coverage report                   │
│   └── agents.yml   → Security Agent + QA Agent auto-run         │
│                       reports uploaded as CI artifacts          │
└─────────────────────────────────────────────────────────────────┘
```

---

## Application Layer — Components


| File                             | Purpose                                                          |
| -------------------------------- | ---------------------------------------------------------------- |
| `app/main.py`                    | FastAPI app, CORS middleware, startup, global exception handler  |
| `app/core/database.py`           | SQLite engine, session factory, table initialisation             |
| `app/core/logging.py`            | Structured JSON logger used across all layers                    |
| `app/core/exceptions.py`         | Domain exceptions — `EventNotFoundError`, `AccountNotFoundError` |
| `app/models/orm.py`              | `Event` + `AuditLog` SQLModel tables                             |
| `app/models/schemas.py`          | Pydantic v2 request/response shapes                              |
| `app/repositories/event_repo.py` | All DB access — ORM only, no raw SQL                             |
| `app/services/event_service.py`  | Business logic — idempotency, balance, ordering                  |
| `app/routes/events.py`           | `POST /events`, `GET /events/{id}`, `GET /events`                |
| `app/routes/accounts.py`         | `GET /accounts/{id}/balance`, `GET /audit-log`                   |


---

## Agent Layer — What Each Agent Produces


| Agent           | Input                                    | Output                                                     |
| --------------- | ---------------------------------------- | ---------------------------------------------------------- |
| Design Agent    | Spec document                            | `docs/architecture.md` — Mermaid diagram + design summary  |
| Dev Agent       | Spec + architecture doc                  | Full application code in `app/`                            |
| Security Agent  | Generated `app/` code                    | `reports/security-review.md`                               |
| QA Agent        | Generated `app/` code + test run results | `tests/` + `reports/coverage.md` + `reports/functional.md` |
| Docs Agent      | Live `/openapi.json` from running app    | `docs/api-guide.md`                                        |
| Changelog Agent | Git log                                  | `CHANGELOG.md`                                             |


---

## Validator Layer — Anti-Hallucination

Validators run after every Dev Agent output. They execute — not read — the generated code.


| Validator           | Executes                             | Catches                            |
| ------------------- | ------------------------------------ | ---------------------------------- |
| `SyntaxValidator`   | `py_compile.compile()`               | Syntax errors                      |
| `LintValidator`     | `ruff check` via subprocess          | Undefined names, bad imports       |
| `ImportValidator`   | `importlib.import_module()`          | Missing packages, circular imports |
| `ServerValidator`   | uvicorn subprocess + httpx `/health` | Startup crashes                    |
| `ContractValidator` | httpx hitting all 4 endpoints        | Wrong status codes, missing fields |
| `TestValidator`     | `pytest` via subprocess              | Logic errors, broken assertions    |


If any validator fails — specific error fed back to Dev Agent — retry up to 3 times — if still failing, pipeline stops for human review.

---

## Data Flow — How an Event Moves Through the System

```
Client POST /events
       │
       ▼
  Pydantic v2 validates payload
  ├── invalid → 422 Unprocessable Entity (structured error, no stack trace)
  └── valid   ──►
                  AuditLog entry written
                  (endpoint, timestamp, account_id, outcome)
                       │
                       ▼
                  eventId lookup
                  ├── exists → return original event, 200 OK  (idempotent)
                  └── new    → INSERT Event row, 201 Created
                                    │
                                    ▼
                             Balance computed live on read
                             SUM(CREDIT) - SUM(DEBIT)
                             ORDER BY eventTimestamp ASC
                             (out-of-order safe — arrival order irrelevant)
```

---

## File Structure

```
event-ledger/
│
├── app/                        # generated by Dev Agent
│   ├── main.py
│   ├── core/
│   │   ├── database.py
│   │   ├── logging.py
│   │   └── exceptions.py
│   ├── models/
│   │   ├── orm.py
│   │   └── schemas.py
│   ├── repositories/
│   │   └── event_repo.py
│   ├── services/
│   │   └── event_service.py
│   └── routes/
│       ├── events.py
│       └── accounts.py
│
├── agents/                     # LangChain pipeline
│   ├── pipeline.py             # run this — orchestrates all agents
│   ├── design_agent.py
│   ├── dev_agent.py
│   ├── security_agent.py
│   ├── qa_agent.py
│   ├── docs_agent.py
│   └── changelog_agent.py
│
├── validators/                 # anti-hallucination sub-agents
│   ├── syntax_validator.py
│   ├── lint_validator.py
│   ├── server_validator.py
│   └── contract_validator.py
│
├── .prompts/                   # versioned prompt files
│   ├── design_agent.md
│   ├── dev_agent_data.md
│   ├── dev_agent_api.md
│   ├── security_agent.md
│   ├── qa_agent.md
│   └── docs_agent.md
│
├── tests/                      # generated by QA Agent
├── reports/                    # generated by Security + QA agents
├── docs/                       # generated by Design + Docs agents
│
├── .github/
│   └── workflows/
│       ├── tests.yml
│       └── agents.yml
│
├── APPROACH.md                 # traditional vs AI-augmented comparison
├── ARCHITECTURE.md             # this file
├── SOLUTION.md                 # per-layer stack decisions
├── PROGRESS.md                 # running phase log
├── CHANGELOG.md                # generated by Changelog Agent
├── README.md
├── pyproject.toml
├── docker-compose.yml
└── .env.example
```

