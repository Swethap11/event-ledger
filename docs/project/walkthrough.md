# Walkthrough: How This Was Built

A first-person account of the decisions, tools, and process behind this submission.

---

## 1. Reading the Handout

The first step was reading the candidate handout carefully and not touching any code.

The requirements were clear: idempotent event submission, out-of-order tolerance, balance calculation, four endpoints. Standard financial ledger pattern. But the interesting constraint was the open-ended nature — no prescribed stack, no prescribed approach.

That gap was the opportunity. So started to build the process first, then let the process build the product.

---

## 2. Choosing the Stack

Before writing a single line of code, I designed the tech stack manually:

- **FastAPI** — idiomatic Python API framework, automatic OpenAPI spec generation, Pydantic v2 native
- **SQLModel** — bridges SQLAlchemy and Pydantic in one model definition, no duplication
- **SQLite** — right-sized for this scope; swappable for Postgres at the repository layer
- **uv** — fast dependency management, lockfile included
- **Ruff** — single linter + formatter, replaces flake8/black/isort
- **LangChain + LangChain OpenAI** — agent orchestration with structured output
- **LangSmith** — full observability on every LLM call, shareable trace URLs
- **pytest + httpx** — test client that hits real endpoints, no mocking
- **GitHub Actions** — CI that runs the same agent scripts as local development

---

## 3. Building the Agent Pipeline

With the stack decided, I designed the pipeline before writing any application code. The pipeline is the meta-layer — it builds and validates the application.

**The structure:**

```
ai_sdlc/
├── agents/      ← LangChain agents, one per SDLC role
├── validators/  ← anti-hallucination executors
├── prompts/     ← versioned prompt files (one per agent/module)
└── runners/     ← phase runners to invoke agents in sequence
```

Each agent has a single job. Each prompt is a separate file versioned, editable, independent of the Python code. The validators do not read generated code, they compile it, lint it, start the server, and hit the endpoints.

**Cursor Agents + Claude(Sonnet 4.6)** were used throughout this phase. Rather than typing boilerplate, I described what each agent needed to do and iterated on the output. Each runner was scaffolded with AI assistance, then refined for my specific requirements, error handling, token limits, retry logic, structured outputs.

The key engineering decisions at this stage:

- One LLM call per module (not per full pipeline) to stay within token limits
- Structured Pydantic outputs from every agent — no free-form text that requires parsing
- System prompt passed as a single variable to avoid LangChain's brace-parsing issues with code blocks
- Validators run in sequence and feed errors back to the agent — not just logging failures but driving retries

---

## 4. Running the Pipeline Phase by Phase

Each phase had a dedicated runner:


| Runner          | What it does                                                                  |
| --------------- | ----------------------------------------------------------------------------- |
| `run_phase2.py` | Design Agent reads spec → produces architecture doc + Mermaid diagram         |
| `run_phase3.py` | Dev Agent generates core, models, repositories — validators after each        |
| `run_phase4.py` | Dev Agent generates services, routes, main — server + contract validation     |
| `run_phase5.py` | Security Agent reviews all app code → security report                         |
| `run_phase6.py` | QA Agent generates tests → runs pytest → coverage report                      |
| `run_phase7.py` | Docs Agent reads live OpenAPI spec → API guide; Changelog Agent reads git log |


**What actually happened during these runs:**

Phase 3 and 4 required the most iteration. The Dev Agent would generate structurally correct code but with subtle issues — wrong field names (camelCase vs snake_case), incorrect import paths, `float` instead of `Decimal`. These failures were caught by validators and fed back. Over several runs, the prompts were tightened to lock in the exact class signatures, field names, and import paths.

Phase 5 (security) surfaced false positives — the agent flagged SQLModel ORM calls as SQL injection risks. The prompt was updated to explicitly state that parameterised ORM calls are not injection vectors.

Phase 6 (QA) hit token limits when trying to generate all test files in one call. Split to one file per LLM call, which solved it.

Phase 7 required the server to be running to fetch the live OpenAPI spec — the runner starts the server, fetches the spec, generates docs, then shuts it down.

---

## 5. What Was Left as Future Scope

Due to time constraints and token/tool availability, some items were scoped down:

**MCP Server** (`mcp_server.py`) — built and functional, but not fully wired. The server exposes all four API endpoints as AI-callable tools. To complete: run `uv sync`, add the Claude Desktop config from the file header. This enables Claude to submit events, query balances, and check health directly.

**Full agentic fix loop in Phase 5** — the security agent was simplified to review-only after the fix loop caused more regressions than it solved. The underlying issue was the Dev Agent regenerating broken code when given a security-focused prompt. Fix: prompts updated, fix loop reserved for the Monitor Agent instead.

**Hypothesis + Schemathesis property testing** — scaffolded in pyproject.toml, removed from QA agent output after token limits. The test suite runs 16 standard pytest cases at 93% coverage.

---

## 6. The Production Monitor

The agents described above are **development tools** — they run once per phase, on a developer machine or in CI. They are not running in production.

The question that followed was: *if this app is running daily in production and something breaks, what happens?*

The answer became the Monitor Agent — a production runtime that closes the loop:

```
FastAPI (ErrorCaptureMiddleware)
       │  5xx captured → logs/errors.jsonl
       ▼
run_monitor.py (polls every 10s)
       │
       ▼
monitor_agent (LangChain)
       │
       ├── TRANSIENT  → log incident report, no change
       ├── SECURITY   → log finding for human review
       ├── TEST_GAP   → log finding for human review
       └── BUG        → apply fix to source → restart server
```

The middleware captures every 5xx with full traceback. The monitor reads new entries, loads the affected source files, calls the agent, and either applies a fix and restarts the server, or writes an incident report for human review.

This is the same agent pattern used in development — now running continuously alongside the application.

---

## 7. What This Could Look Like at Scale

The current implementation is a working proof of concept. In a corporate environment, several adaptations would be natural:

**Tech stack swap** — the application layer is deliberately separated from the agent layer. Swapping SQLite for Postgres, FastAPI for Django REST Framework, or pytest for a corporate test framework requires updating the Dev Agent prompts and validators — not the agent logic itself.

**Automated runner triggers** — currently the phase runners are invoked manually. In a corporate pipeline they could be triggered by:

- A git push to a feature branch (GitHub Actions already wired)
- A scheduled job (cron or workflow scheduler) for nightly security + QA sweeps
- A webhook from a ticket system when a new requirement lands

**MCP server as the agent interface** — the `mcp_server.py` exposes the Event Ledger API as AI-callable tools. Extended, this pattern means agents don't interact with the system through shell commands — they call typed tools with structured inputs. Instead of `uv run python ai_sdlc/runners/run_phase5.py`, an orchestrating agent calls `run_security_review(files=[...])` as a tool.

**Human-in-the-loop on fixes** — the Monitor Agent currently applies fixes automatically if confidence ≥ 0.7. In a production environment, the fix workflow would be:

1. Monitor Agent detects error, generates fix
2. Creates a pull request with the fix and the incident report as the PR description
3. Human reviews and approves
4. Merge triggers CI — tests + security agent run on the fix before it reaches prod

This is achievable with the existing architecture — the `apply_fix()` function in `run_monitor.py` would call `gh pr create` instead of writing directly to disk.

**The result** is a system where AI agents handle the repetitive, systematic work — error detection, fix generation, documentation, security sweeps — while humans retain decision authority on what goes to production.