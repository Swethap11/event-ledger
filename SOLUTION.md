# Proposed Solution: Stack Decisions

## Overview

This document explains the tool chosen at every layer, the alternatives considered, and why the final choice was made. Where a tool sounds complex, that complexity is called out explicitly — along with when it would actually be justified.

---

## Layer 1: Language

### Options Considered

| Option | Pros | Cons | Complexity |
|---|---|---|---|
| **Python 3.12** | Readable, fast iteration, strongest AI/ML ecosystem, LangChain native | GIL limits true parallelism | Low |
| Java | Strong typing, mature Spring Boot ecosystem | Verbose, slower to write 4 endpoints | Low–Medium |
| C# | Modern .NET, good typing, ASP.NET is solid | Less idiomatic for this kind of API | Low–Medium |

### Decision: Python 3.12

The spec allows all three. Python wins because LangChain, all validators, and all testing tools are Python-native. Using another language would mean two separate runtimes — one for the app, one for the agents. Python keeps everything in one ecosystem.

---

## Layer 2: Web Framework

### Options Considered

| Option | Auto Docs | Validation | Async | Complexity |
|---|---|---|---|---|
| **FastAPI** | Yes — OpenAPI/Swagger free | Pydantic native | Yes | Low |
| Flask | No | Manual | No (without extensions) | Low |
| Django REST | No | Serializers (verbose) | Partial | Medium |

### Decision: FastAPI

FastAPI generates a `/docs` Swagger UI and `/openapi.json` automatically from Pydantic models. The Schemathesis contract tester reads that spec directly. Documentation Agent reads it to generate the API guide. Every downstream tool benefits from the auto-generated spec — this is not a coincidence, it is the architecture.

**Flask** is simpler but gives nothing for free. Every validation, every error response, every schema is hand-written.

**Django REST** is the right choice for a full-featured product with admin panels, auth, and ORM at scale. Overkill for four endpoints.

---

## Layer 3: Database

### Options Considered

| Option | Embedded | Spec Compliant | Signal | Complexity |
|---|---|---|---|---|
| **SQLite + SQLModel** | Yes | Yes | High | Low |
| DuckDB | Yes | Yes | Very high | Low–Medium |
| PostgreSQL | No — needs server | No — violates spec | Standard | Medium |
| PostgreSQL + pgvector | No | No | Overkill | High |

### Decision: SQLite + SQLModel

SQLite is embedded — no external process, no setup, no configuration. The spec explicitly requires this.

SQLModel (by the FastAPI author) merges SQLAlchemy ORM and Pydantic into one class definition. Without it, you maintain two parallel classes for every entity — one for the database, one for the API. SQLModel eliminates that duplication where the shapes are the same.

ORM-only access means SQL injection is structurally impossible — there are no raw query strings anywhere.

**Why not DuckDB:** DuckDB is a columnar store optimised for analytical aggregations. The balance query (`SUM(amount)`) would be marginally faster at large scale. For a take-home with hundreds of events at most, the gain is invisible. DuckDB is the right swap if this ledger ever needed to process millions of events or run time-series analytics. It is not the right choice here.

**Why not PostgreSQL + pgvector:** PostgreSQL requires an external server — disqualified by the spec. pgvector adds vector similarity search. There is nothing to embed in a financial event — no free-text fields, no semantic search requirement. This would be adding a capability with no corresponding need.

---

## Layer 4: Validation

### Options Considered

| Option | Declarative | Built into FastAPI | Strict Mode | Complexity |
|---|---|---|---|---|
| **Pydantic v2** | Yes | Yes — native | Yes | Low |
| Manual if/else checks | No | N/A | As strict as you write | Low |
| Marshmallow | Yes | No | Partial | Low–Medium |

### Decision: Pydantic v2 strict mode

Validation lives in the schema, not in route handlers. The constraints are declarative and co-located with the data definition:

```python
amount: Annotated[float, Field(gt=0)]
type: Literal["CREDIT", "DEBIT"]
```

Pydantic v2 with `extra="forbid"` rejects unknown fields — a client cannot sneak unexpected data through. Validation errors produce structured JSON automatically, with field-level detail. No hand-written error formatting needed.

---

## Layer 5: Agent Orchestration

### Options Considered

| Option | Model | Best For | GitHub Models Support | Complexity |
|---|---|---|---|---|
| **LangChain** | Chain composition | Sequential pipelines, tool use, structured output | Yes — via langchain-openai | Medium |
| CrewAI | Role-based agents | Multi-agent collaboration with defined roles | Yes | Low–Medium |
| LangGraph | State machine | Complex branching, loops, conditional flows | Yes | High |
| Plain Python + httpx | No framework | Simple one-shot LLM calls | Yes | Low |

### Decision: LangChain

LangChain Expression Language (LCEL) uses the pipe operator to compose chains:

```python
chain = prompt | llm.with_structured_output(ArchitectureDoc) | file_writer
```

Each agent is a chain. Chains are composable, testable, and type-safe via Pydantic structured outputs. LangChain also provides the callback system used by LangSmith for tracing — this is built in, not bolted on.

**Why not CrewAI:** CrewAI's role-based model maps well to our agent names, but it is a higher-level abstraction with less control over prompts and output parsing. At this scale, we want precise control over what each agent receives and returns.

**Why not LangGraph:** LangGraph is designed for stateful workflows with branching and conditional edges. Our pipeline is sequential — Design → Dev → Security → QA → Docs. LangGraph's complexity is not justified for a linear pipeline.

**Why not plain Python:** Plain Python is the right call for simple one-shot calls. The moment you add structured output parsing, retry logic, callbacks, and tool use, you are reinventing a subset of LangChain. The framework earns its place here.

---

## Layer 6: LLM Provider

### Options Considered

| Option | Cost | Setup | Model Quality | Rate Limits | Complexity |
|---|---|---|---|---|---|
| **GitHub Models** | Free | GitHub token — already have it | GPT-4o-mini, Llama 3.3 70B | 15 req/min, 150k tokens/day | Low |
| Groq | Free tier | New account required | Llama 3.3 70B, Mixtral | Generous | Low |
| Ollama | Free — local | Install Ollama + pull model | Llama 3.2, Mistral | None | Medium |
| Claude API | Paid | Anthropic account | Claude Sonnet/Haiku | Per tier | Low |

### Decision: GitHub Models (GPT-4o-mini)

GitHub Models is OpenAI-compatible — `langchain-openai` connects to it with a single base URL change and the GitHub token the reviewer already has from cloning the repo. No new accounts, no new credentials.

GPT-4o-mini is well-suited for structured code generation. It follows system prompts reliably, handles Pydantic structured output correctly, and is fast enough for a pipeline of 10–15 calls.

**Rate limit mitigation:** Agent outputs are cached to disk. If the output file exists and `--force` is not passed, the LLM call is skipped. This keeps re-runs cheap during development.

---

## Layer 7: Observability

### Options Considered

| Option | What It Gives | Cost | Complexity |
|---|---|---|---|
| **LangSmith** | Full trace of every LLM call — prompt, response, latency, tokens. Shareable URL. | Free tier | Low — one env var |
| Custom logging | Partial — you log what you remember to log | Free | Medium |
| None | Nothing | Free | None |

### Decision: LangSmith

LangSmith produces a URL the reviewer can click to see every AI decision made during the pipeline run. This is the most direct way to demonstrate AI-augmented SDLC — show the reasoning, not just the output.

One environment variable enables it:
```
LANGCHAIN_TRACING_V2=true
LANGCHAIN_API_KEY=your_free_key
```

No code changes required.

---

## Layer 8: Anti-Hallucination Validators

No alternatives considered here — this layer is non-negotiable. Agent output that is not validated before commit is a liability.

| Validator | Executes | Catches |
|---|---|---|
| `SyntaxValidator` | `py_compile.compile()` | Syntax errors |
| `LintValidator` | `ruff check` via subprocess | Undefined names, bad imports |
| `ImportValidator` | `importlib.import_module()` | Missing packages, circular imports |
| `ServerValidator` | `uvicorn` subprocess + httpx `/health` | Startup crashes, port conflicts |
| `ContractValidator` | httpx hitting all 4 endpoints | Wrong status codes, missing fields |
| `TestValidator` | `pytest` via subprocess | Logic errors, broken assertions |

If any validator fails, the specific error is fed back to the Dev Agent for a fix. Maximum 3 retries. If still failing after 3, the pipeline stops and flags for human review.

---

## Layer 9: Testing

| Tool | Type | Why |
|---|---|---|
| pytest | Unit + integration | Standard, readable, well-supported |
| pytest-cov | Coverage | Required deliverable — coverage reports |
| Hypothesis | Property-based | Auto-generates edge cases for ordering and balance logic |
| Schemathesis | Contract/OpenAPI | Reads the FastAPI-generated spec, fires hundreds of malformed requests |

Three layers because each catches a different class of bug. Schemathesis in particular catches things no human would think to write — it generates inputs from the schema definition itself.

---

## Layer 10: Package Management and Tooling

| Tool | Replaces | Why |
|---|---|---|
| uv | pip + venv + requirements.txt | 10–100x faster installs, single lockfile, one config |
| Ruff | flake8 + black + isort | One tool, one config block, extremely fast |

Both are from Astral. Both are the modern standard in Python tooling as of 2024–2025.

---

## Layer 11: CI/CD

### Options Considered

| Option | Complexity | Justification |
|---|---|---|
| **GitHub Actions** | Low | Already on GitHub, free, agents run on push |
| Jenkins | High | Self-hosted, overkill |
| None | None | Misses the CI demonstration |

### Decision: GitHub Actions

Two workflows:
- `agents.yml` — runs Security Agent and QA Agent on every push, uploads reports as artifacts
- `tests.yml` — runs pytest + coverage on every push

Both are generated by the Dev Agent as part of the pipeline.

---

## What is Not in This Solution (and Why)

| Not Included | Why | When It Would Be Justified |
|---|---|---|
| FAISS / vector search | Spec is 144 lines — inject it directly into the prompt | If the knowledge base were thousands of pages of internal docs |
| LangGraph | Pipeline is sequential — no branching needed | If agents needed to loop conditionally or make routing decisions |
| CrewAI | Less control over prompts and output than LCEL | If you want rapid role-based prototyping without caring about prompt internals |
| PostgreSQL | Violates spec constraint — requires external server | Production deployment with concurrent writes and real scale |
| pgvector | No semantic search requirement exists | If event metadata had free-text descriptions that needed similarity search |
| Redis | No caching requirement — SQLite handles the load | High-throughput production ledger with thousands of concurrent users |
| Alembic | `SQLModel.metadata.create_all()` is sufficient for one schema version | When schema evolves in production and zero-downtime migrations are needed |
| Celery | All operations are synchronous and fast | If balance computation or event processing became long-running background work |

---

## Future Scope

| When This Scales | Consider |
|---|---|
| Millions of events per account | Swap SQLite for DuckDB — columnar aggregations make balance queries dramatically faster |
| Multiple concurrent writers | PostgreSQL with advisory locks or `SELECT FOR UPDATE` |
| Real production deployment | Alembic for migrations, PostgreSQL, connection pooling |
| Complex agent workflows | LangGraph — conditional routing, retry branches, parallel agent execution |
| Larger knowledge base for agents | FAISS or Chroma for RAG — when context exceeds what fits in a prompt |
| Agent cost management at scale | LiteLLM — model routing, cost caps, fallback providers |
| Semantic search over event metadata | pgvector — if free-text metadata fields are added and similarity search is needed |
| Automated deployment | Add a Deploy Agent to the pipeline — generates Kubernetes manifests or Terraform config |
