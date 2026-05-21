# Approach: Traditional vs AI-Augmented SDLC

## The Task

Build an **Event Ledger API** for a financial services context. Four REST endpoints, two core guarantees: idempotency and out-of-order event tolerance with full test coverage, documentation, and a clean commit history.

This is a standard backend engineering task. This submission is *how* it is built — using AI agents to drive each stage of the software development lifecycle, not just as a coding assistant or chatbot.

---

## Traditional Way

A developer sits down, reads the spec, and manually produces every artifact:

1. Reads the spec and sketches a design mentally or on paper
2. Chooses a framework and sets up the project
3. Writes models, routes, services, and tests by hand
4. Reviews their own code for security issues
5. Writes documentation manually — often skipped or minimal
6. Commits with whatever message feels right in the moment
7. Submits

Takes multiple sprints for a developer team. The output is entirely dependent on the individual — their experience, their energy, and their choices that day.

---

## The AI-Augmented Way

A pipeline of specialised AI agents, each with a defined role, drives each SDLC stage. The developer designs the agents, writes the prompts, and reviews the output — but the agents do the generation, validation, and reporting.

```
Spec ──► Design Agent      → architecture doc + Mermaid diagram
         Dev Agent         → working application code (self-healing loop)
         Security Agent    → security review report
         QA Agent          → tests + coverage + functional report
         Docs Agent        → API usage guide
         Changelog Agent   → structured CHANGELOG.md

         Validators run after every Dev Agent output:
         Syntax → Lint → Import → Server start → Contract → Tests
```

Every artifact is produced by an agent. Every agent output is validated before it touches the repo. The developer's role shifts from writing to directing and reviewing.

### What Looks the Same — and What Is Different

The final application code — the FastAPI routes, SQLModel tables, Pydantic schemas, pytest tests — will look structurally similar to what a developer would write by hand. That is intentional. The output is not the differentiator. The process is.

What changes is who produces it, how it is verified, and how long it takes:

- The **Design Agent** decides the architecture — which pattern fits the problem, how layers should be separated, what the Mermaid diagram should show
- The **Dev Agent** writes the code — models, routes, services, repositories — and runs a self-healing loop against Ruff until the output is lint-clean before it is ever committed
- The **Security Agent** reviews every generated file independently, as a second set of eyes that was not involved in writing the code
- The **QA Agent** approaches the code as a black box — generates tests, runs them, and produces a coverage report without knowing what the developer intended
- The **Validators** do not read the code — they compile it, import it, start the server, and hit the endpoints with real HTTP calls. Plausible-looking code that does not run is caught before it reaches the repo

Setting up this pipeline is where the effort goes. Once it exists, every stage of the SDLC — design, development, security review, testing, documentation, changelog — runs automatically. What would take a developer team days of back-and-forth across standups, PR reviews, and documentation sprints is compressed into a single pipeline run.

### How the Pipeline Integrates With the Tech Stack

The agents do not work in isolation — each one produces output that feeds directly into the chosen tech stack:

| Agent | Integrates With |
|---|---|
| Design Agent | Reads the spec, produces architecture that matches FastAPI's layered structure |
| Dev Agent | Generates FastAPI routes, SQLModel ORM models, Pydantic v2 schemas, SQLite setup |
| Validators | Run Ruff (linter), start uvicorn (server), hit FastAPI endpoints via httpx |
| QA Agent | Generates pytest + Hypothesis + Schemathesis tests — reads the FastAPI OpenAPI spec for contract tests |
| Security Agent | Reviews SQLAlchemy ORM usage, Pydantic strict mode, FastAPI exception handlers — stack-aware |
| Docs Agent | Reads `/openapi.json` from the running FastAPI instance — generates docs from the live spec |
| Changelog Agent | Reads git history — formats output per commit messages the Dev Agent produced |
| LangSmith | Traces every LangChain agent call — integrated at the orchestration layer with zero code changes |
| GitHub Actions | Runs Security and QA agents on every push — same scripts locally and in CI |

The pipeline is not a layer on top of the stack. It builds the stack, validates it, and integrates with it at every stage.

---

## Comparison

| Metric | Traditional | AI-Augmented | Notes |
|---|---|---|---|
| **Effort** | High — developer writes all code, docs, tests manually | Medium — developer writes prompts, reviews output, fixes validators | Effort shifts from generation to orchestration |
| **Timeline** | Multiple sprints | Hours once pipeline is running | Pipeline setup is a one-time cost |
| **Consistency** | Developer-dependent — varies by mood, fatigue, experience | High — same prompt produces consistent structure every run | Agents don't skip logging or error handling when tired |
| **Documentation** | Frequently skipped or thin | Automated — Docs Agent generates from OpenAPI spec | Quality depends on prompt quality |
| **Security review** | Manual, usually informal | Security Agent reviews every file systematically | Not a replacement for a real security audit, but catches common issues automatically |
| **Test coverage** | Written by the same person who wrote the code — blind spots exist | QA Agent approaches code as a black box, generates edge cases independently | Hypothesis + Schemathesis add property-based and contract testing |
| **Commit history** | Ad hoc — "fix bug", "wip", "update" | Dev Agent generates structured, meaningful commit messages per module | Directly addresses the "meaningful commit history" requirement |
| **Cost** | Developer time only — hours × hourly rate | Near-zero LLM cost (GitHub Models free tier) + developer time | GitHub Models: 150k tokens/day free |
| **Reliability** | High if developer is experienced | Medium-High — validators catch hallucinations before code reaches repo | Self-healing loop retries up to 3 times on failure |
| **Dependency** | Low — just the chosen framework | Medium — LangChain, GitHub Models, LangSmith, validators | Each dependency is justified; none are decorative |
| **Auditability** | None — no record of decisions made | LangSmith trace URL records every LLM call, prompt, and response | Shareable — reviewer can see AI reasoning |
| **Reproducibility** | Not reproducible — different developer, different output | High — same prompts, same model, same output structure | Prompt files are version-controlled |
| **Maintainability** | High if developer wrote clean code | Medium — generated code must be reviewed before committing | Validators enforce Ruff linting on all generated code |
| **Scalability of process** | Does not scale — one developer, one SDLC | Scales — add a new agent for a new stage without changing others | Each agent is independent |
| **Human oversight** | Developer is both author and reviewer | Developer reviews agent output at each stage — not auto-committed | Human stays in the loop |

---

## Where Traditional Still Wins

- **Simple, well-scoped tasks** — for a 20-line script, the agent pipeline is overkill
- **Novel problem domains** — agents hallucinate more on things not well-represented in training data
- **Real-time debugging** — a human developer debugs interactively; agents work in batches
- **Judgment calls** — "should this be a 400 or a 422?" — a developer decides instantly; an agent needs a prompt that anticipates the question

---

## Where AI-Augmented Wins

- **Consistency at scale** — same logging, same error handling, same commit message style across every module
- **Coverage of the boring parts** — documentation, security checklists, changelogs — things developers skip
- **Demonstrating process** — the pipeline is itself an artifact that shows how the team works, not just what they built
- **Onboarding** — a new developer can read the prompts and understand the coding standards immediately

---

## Conclusion

This comparison is not meant to suggest the traditional approach is wrong. Traditional development remains proven and reliable — especially when the problem is small or requires fine-grained judgment in the moment. What changes with AI is the economics of effort once the pipeline is in place.

After the one-time setup — agents, prompts, validators, and observability — the day-to-day work becomes faster and less manual. Developers spend less time generating artifacts and more time directing the process and making decisions that require human judgment.

That does not remove the need for engineers. It raises the bar for what they must know. Reviewing agent output, debugging failures, and knowing where a model can hallucinate requires deeper understanding than writing the code yourself. Awareness is the safety layer: AI accelerates delivery, but human oversight keeps the output trustworthy.
