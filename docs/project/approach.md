# Approach: AI-Augmented SDLC

## The Task

Build an **Event Ledger API** for a financial services context — four REST endpoints, two core guarantees: idempotency and out-of-order event tolerance, with full test coverage, documentation, and a clean commit history.

This submission is not just the working API. It is the **process used to build it** — a pipeline of specialised AI agents, each with a defined role, driving each stage of the software development lifecycle. The developer designs the agents, writes the prompts, and reviews the output. The agents do the generation, validation, and reporting.

---

## The Pipeline

```
Spec ──► Design Agent      → architecture doc + Mermaid diagram
         Dev Agent         → working application code (self-healing loop)
         Security Agent    → security review report
         QA Agent          → tests + coverage + functional report
         Docs Agent        → API usage guide
         Changelog Agent   → structured CHANGELOG.md
         Monitor Agent     → production error classification + auto-fix

         Validators run after every Dev Agent output:
         Syntax → Lint → Import → Server start → Contract → Tests
```

Every artifact is produced by an agent. Every agent output is validated before it touches the repo. The developer's role shifts from writing to directing and reviewing.

---

## What Each Agent Does

**Design Agent** decides the architecture — which pattern fits the problem, how layers should be separated, how the data flows. Outputs a Mermaid diagram and a component breakdown that the Dev Agent uses as its blueprint.

**Dev Agent** writes the code — models, routes, services, repositories — one module at a time. After each module, validators compile it, run Ruff lint, start the server, and hit the endpoints with real HTTP calls. If anything fails, the error is fed back to the agent and it retries (up to 3 times). Plausible-looking code that does not run is caught before it is ever committed.

**Security Agent** reviews every generated file independently — as a second set of eyes that was not involved in writing the code. It was not in the room when the code was written, so it has no blind spots.

**QA Agent** approaches the code as a black box. It generates pytest tests, runs them, and produces a coverage report without knowing what the developer intended. 93% coverage achieved on first run.

**Docs Agent** reads the live `/openapi.json` from the running server and generates a developer-facing API guide from the actual endpoints — not from what the spec said they should be.

**Changelog Agent** reads the git log and generates a structured CHANGELOG.md in Keep a Changelog format, using the meaningful commit messages the Dev Agent produced per module.

**Monitor Agent** *(production)* — watches the live server's error log. When a 5xx is captured, it classifies the error (BUG / SECURITY / TEST_GAP / TRANSIENT), generates a targeted fix, applies it to disk, and restarts the server. The first self-healing production system built as part of this exercise.

---

## The Validator Layer — Anti-Hallucination

The validators do not read the generated code — they execute it. This is the key distinction.

| Validator | Executes | Catches |
|---|---|---|
| SyntaxValidator | `py_compile.compile()` | Syntax errors |
| LintValidator | `ruff check` via subprocess | Undefined names, bad imports |
| ServerValidator | uvicorn subprocess + httpx `/health` | Startup crashes |
| ContractValidator | httpx hitting all 4 endpoints | Wrong status codes, missing fields |

A model that generates code that looks right but does not run is useless for production. The validators make this impossible to miss.

---

## How the Pipeline Integrates With the Tech Stack

The agents do not work in isolation — each one produces output that feeds directly into the chosen stack:

| Agent | Integrates With |
|---|---|
| Design Agent | Reads the spec, produces architecture matching FastAPI's layered structure |
| Dev Agent | Generates FastAPI routes, SQLModel ORM models, Pydantic v2 schemas |
| Validators | Run Ruff, start uvicorn, hit FastAPI endpoints via httpx |
| QA Agent | Generates pytest tests — reads FastAPI OpenAPI spec for contract tests |
| Security Agent | Reviews SQLAlchemy ORM usage, Pydantic strict mode, FastAPI exception handlers |
| Docs Agent | Reads `/openapi.json` from the running FastAPI instance |
| Changelog Agent | Reads git history — formats per commit messages the Dev Agent produced |
| LangSmith | Traces every LangChain agent call — integrated at the orchestration layer |
| GitHub Actions | Runs Security and QA agents on every push — same scripts locally and in CI |

---

## The Shift in Developer Role

Setting up this pipeline is where the effort goes. Once it exists, every stage of the SDLC — design, development, security review, testing, documentation, changelog — runs automatically.

The developer's work becomes:
- Designing agents and writing prompts (the real engineering)
- Reviewing agent output at each stage
- Fixing validators when they catch hallucinations
- Directing the process, not generating the artifacts

This does not remove the need for engineers. It raises the bar for what they must know. Reviewing agent output, debugging failures, and knowing where a model will hallucinate requires deeper understanding than writing the code yourself. Awareness is the safety layer — AI accelerates delivery, but human oversight keeps the output trustworthy.
