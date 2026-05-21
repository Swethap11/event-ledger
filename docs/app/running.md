# Running the Event Ledger API

## Prerequisites

- Python 3.12+
- [uv](https://docs.astral.sh/uv/) — installed automatically by the startup scripts if missing

---

## Quickest Start

```bash
# Linux / Mac
./scripts/start.sh

# Windows PowerShell
.\scripts\start.ps1
```

Both scripts check for `uv`, install dependencies, then start the server at `http://localhost:8000`.

---

## Manual Start

```bash
# Install dependencies
uv sync

# Start the API (development mode with auto-reload)
uv run uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

---

## Configuration

Copy `.env.example` to `.env` and set values as needed:

```bash
cp .env.example .env
```

| Variable | Default | Purpose |
|---|---|---|
| `DATABASE_URL` | `sqlite:///./ledger.db` | SQLite database path |
| `GITHUB_TOKEN` | — | Required only for running AI agent pipeline |
| `LANGCHAIN_API_KEY` | — | Optional — enables LangSmith tracing |
| `LANGCHAIN_TRACING_V2` | `false` | Set `true` to trace all LLM calls |

The API runs without a `.env` file — SQLite is created automatically on first startup.

---

## Docker

```bash
# Start with persistent SQLite volume
docker compose up

# Build and start (first time or after code changes)
docker compose up --build
```

API available at `http://localhost:8000`. Data persists in the `ledger_data` Docker volume.

To stop:
```bash
docker compose down
```

---

## With Agentic Production Monitor

Instead of starting the server directly, run the monitor — it starts the server and watches for errors automatically:

```bash
uv run python ai_sdlc/runners/run_monitor.py
```

Requires `OPENAI_API_KEY` (or `GITHUB_TOKEN` for GitHub Models) in `.env`.

---

## Running Tests

```bash
uv run pytest tests/ --cov=app --cov-report=term-missing
```

Expected: 16 tests, 93% coverage.

```bash
# Run a specific test file
uv run pytest tests/test_idempotency.py -v
```

---

## Interactive API Docs

Once the server is running:

| URL | Contents |
|---|---|
| `http://localhost:8000/docs` | Swagger UI — try all endpoints interactively |
| `http://localhost:8000/redoc` | ReDoc API reference |
| `http://localhost:8000/openapi.json` | Raw OpenAPI spec |
