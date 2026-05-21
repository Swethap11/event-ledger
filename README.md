# event-ledger

Event Ledger API — an idempotent financial transaction service built with an **AI-augmented SDLC** pipeline.

## What it does

REST API for ingesting financial events with guarantees for:

- **Idempotency** — duplicate `eventId` returns the existing record
- **Out-of-order delivery** — reads ordered by `eventTimestamp`, not arrival time
- **Balance correctness** — derived from the event log on read

| Method | Endpoint | Purpose |
|---|---|---|
| `POST` | `/events` | Ingest a transaction event |
| `GET` | `/events/{id}` | Fetch a single event |
| `GET` | `/events?account={accountId}` | List events for an account |
| `GET` | `/accounts/{accountId}/balance` | Net balance (credits − debits) |

## Stack

- **Python 3.12** · **FastAPI** · **SQLModel** · **SQLite**
- **LangChain** agent pipeline (design, dev, security, QA, docs, changelog)
- **Validators** — syntax, lint, server start, OpenAPI contract
- **Testing** — pytest, Hypothesis, Schemathesis

## Docs

| File | Contents |
|---|---|
| [APPROACH.md](APPROACH.md) | Traditional vs AI-augmented SDLC comparison |
| [ARCHITECTURE.md](ARCHITECTURE.md) | System design and agent pipeline |
| [SOLUTION.md](SOLUTION.md) | Stack decisions per layer |
| [PROGRESS.md](PROGRESS.md) | Build progress ledger |

## Quick start

```bash
# Install dependencies (uv recommended)
uv sync --extra dev --extra agents

# Copy env template and add your GitHub Models token
cp .env.example .env

# Run the agent pipeline (generates app code + reports)
python -m agents.pipeline

# Or run the API directly once app/ is generated
uvicorn app.main:app --reload
```

API docs: `http://localhost:8000/docs`

## Repository

https://github.com/Swethap11/event-ledger
