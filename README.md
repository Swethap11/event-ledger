# event-ledger

Event Ledger API — an idempotent financial transaction service built with an **AI-augmented SDLC** pipeline.

## What it does

REST API for ingesting financial events with guarantees for:

- **Idempotency** — duplicate `eventId` returns the existing record (`200`), no double-counting
- **Out-of-order delivery** — reads ordered by `eventTimestamp ASC`, not arrival time
- **Balance correctness** — `Decimal` precision, derived from the full event log on read
- **Audit trail** — every API call writes an immutable `AuditLog` row

| Method | Endpoint | Status | Purpose |
|---|---|---|---|
| `POST` | `/events` | `201` / `200` | Ingest a transaction event |
| `GET` | `/events/{id}` | `200` / `404` | Fetch a single event |
| `GET` | `/events?account={accountId}` | `200` | List events for an account |
| `GET` | `/accounts/{accountId}/balance` | `200` / `404` | Net balance (credits − debits) |
| `GET` | `/health` | `200` | Health check |

## Stack

- **Python 3.12** · **FastAPI** · **SQLModel** · **SQLite**
- **LangChain** agent pipeline (design, dev, security, QA, docs, changelog)
- **GitHub Models** (gpt-4o-mini) — free LLM via OpenAI-compatible endpoint
- **LangSmith** — tracing and evaluations
- **Validators** — syntax, lint (Ruff), server start, OpenAPI contract (httpx)
- **Testing** — pytest + pytest-cov, 16 tests, 93% coverage

## Quick Start

```bash
# Install dependencies and start (auto-detects uv, installs if missing)
./scripts/start.sh          # Linux / Mac
.\scripts\start.ps1         # Windows PowerShell

# Or manually:
uv sync --extra dev --extra agents
cp .env.example .env   # add your GitHub Models token
uv run uvicorn app.main:app --reload
```

API docs: http://localhost:8000/docs

### Run tests

```bash
uv run pytest tests/ --cov=app --cov-report=term-missing
```

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

curl http://localhost:8000/accounts/acct-123/balance
```

## Docker

```bash
docker compose up
```

API available at http://localhost:8000

## Agent Pipeline

```
Design Agent → Dev Agent (×6 modules) → Security Agent → QA Agent → Docs + Changelog
     ↓                 ↓                      ↓               ↓
architecture.md   app/ (16 files)      security-review.md  16 tests, 93% coverage
                  contract-validated
```

Run individual phases:

```bash
uv run python ai_sdlc/runners/run_phase2.py   # Design Agent
uv run python ai_sdlc/runners/run_phase3.py   # Dev — core, models, repositories
uv run python ai_sdlc/runners/run_phase4.py   # Dev — services, routes, main
uv run python ai_sdlc/runners/run_phase5.py   # Security review
uv run python ai_sdlc/runners/run_phase6.py   # QA tests
uv run python ai_sdlc/runners/run_phase7.py   # Docs + changelog
uv run python ai_sdlc/runners/run_monitor.py  # Production monitor (starts server + watches for errors)
```

Requires `GITHUB_TOKEN` in `.env` (see `.env.example`).

## Docs

**Project — AI-augmented SDLC**
| File | Contents |
|---|---|
| [docs/project/walkthrough.md](docs/project/walkthrough.md) | How this was built — decisions, tools, what happened |
| [docs/project/approach.md](docs/project/approach.md) | AI-augmented SDLC pipeline and agent roles |
| [docs/project/architecture.md](docs/project/architecture.md) | System design, Mermaid diagram, data flow |
| [docs/project/stack.md](docs/project/stack.md) | Stack decisions per layer with alternatives considered |

**Application**
| File | Contents |
|---|---|
| [docs/app/running.md](docs/app/running.md) | How to start, configure, and run the API |
| [docs/app/api-reference.md](docs/app/api-reference.md) | Endpoints, request/response, expected behaviour |

**Other**
| File | Contents |
|---|---|
| [docs/project/progress.md](docs/project/progress.md) | Build progress ledger |
| [CHANGELOG.md](CHANGELOG.md) | Release history |

## Repository

https://github.com/Swethap11/event-ledger
