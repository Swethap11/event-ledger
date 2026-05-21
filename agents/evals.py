"""
LangSmith evaluations for agent output quality.
Run: python agents/evals.py

Measures:
- Dev Agent: does generated code have valid Python syntax?
- Dev Agent: does generated code contain no placeholders?
- Security Agent: does it cover all required check areas?
- QA Agent: does it generate tests for all 4 required scenarios?
"""

import os
import re
import py_compile
import tempfile
from pathlib import Path
from langsmith import Client
from langsmith.evaluation import evaluate, EvaluationResult
from langsmith.schemas import Run, Example


# ── Evaluator functions ────────────────────────────────────────────────────────

def eval_syntax_valid(run: Run, example: Example) -> EvaluationResult:
    """Score 1.0 if generated code is syntactically valid Python, else 0.0."""
    code = run.outputs.get("content", "") if run.outputs else ""
    if not code.strip():
        return EvaluationResult(key="syntax_valid", score=0.0, comment="Empty output")

    with tempfile.NamedTemporaryFile(suffix=".py", mode="w", delete=False, encoding="utf-8") as f:
        f.write(code)
        tmp = f.name
    try:
        py_compile.compile(tmp, doraise=True)
        return EvaluationResult(key="syntax_valid", score=1.0)
    except py_compile.PyCompileError as e:
        return EvaluationResult(key="syntax_valid", score=0.0, comment=str(e))
    finally:
        os.unlink(tmp)


def eval_no_placeholders(run: Run, example: Example) -> EvaluationResult:
    """Score 1.0 if generated code contains no placeholder patterns."""
    code = run.outputs.get("content", "") if run.outputs else ""
    placeholders = ["TODO", "FIXME", "NotImplementedError", "your_code_here", "<FILL"]
    found = [p for p in placeholders if p.lower() in code.lower()]
    if found:
        return EvaluationResult(
            key="no_placeholders",
            score=0.0,
            comment=f"Found placeholders: {found}",
        )
    return EvaluationResult(key="no_placeholders", score=1.0)


def eval_security_coverage(run: Run, example: Example) -> EvaluationResult:
    """Score based on how many required security areas the Security Agent covered."""
    report = run.outputs.get("summary", "") if run.outputs else ""
    required_areas = [
        "sql injection",
        "input validation",
        "stack trace",
        "audit",
        "idempotency",
    ]
    covered = [area for area in required_areas if area.lower() in report.lower()]
    score = len(covered) / len(required_areas)
    return EvaluationResult(
        key="security_coverage",
        score=score,
        comment=f"Covered {len(covered)}/{len(required_areas)}: {covered}",
    )


def eval_qa_scenario_coverage(run: Run, example: Example) -> EvaluationResult:
    """Score based on how many required test scenarios the QA Agent generated."""
    test_content = run.outputs.get("content", "") if run.outputs else ""
    required_scenarios = [
        "idempotency",
        "ordering",
        "balance",
        "validation",
    ]
    covered = [s for s in required_scenarios if s.lower() in test_content.lower()]
    score = len(covered) / len(required_scenarios)
    return EvaluationResult(
        key="qa_scenario_coverage",
        score=score,
        comment=f"Covered {len(covered)}/{len(required_scenarios)}: {covered}",
    )


# ── Dataset builder ────────────────────────────────────────────────────────────

def build_dev_agent_dataset(client: Client, dataset_name: str = "dev-agent-evals") -> str:
    """Create a LangSmith dataset of Dev Agent inputs and expected outputs."""
    if any(d.name == dataset_name for d in client.list_datasets()):
        print(f"[Evals] Dataset '{dataset_name}' already exists — skipping creation.")
        return dataset_name

    dataset = client.create_dataset(
        dataset_name=dataset_name,
        description="Evaluates Dev Agent code generation quality",
    )

    spec = Path("event-ledger-candidate-handout.md")
    spec_text = spec.read_text(encoding="utf-8") if spec.exists() else "Event Ledger API spec"

    client.create_examples(
        inputs=[
            {"module": "core", "spec": spec_text},
            {"module": "models", "spec": spec_text},
            {"module": "repositories", "spec": spec_text},
        ],
        outputs=[
            {"expected": "syntactically valid Python with database.py, logging_config.py, exceptions.py"},
            {"expected": "syntactically valid Python with Event and AuditLog SQLModel tables and Pydantic schemas"},
            {"expected": "syntactically valid Python with EventRepository class and write_audit method"},
        ],
        dataset_id=dataset.id,
    )

    print(f"[Evals] Dataset '{dataset_name}' created with {3} examples.")
    return dataset_name


# ── Run evaluations ────────────────────────────────────────────────────────────

def run_dev_agent_evals() -> None:
    """Run Dev Agent evaluations and print results."""
    if not os.environ.get("LANGCHAIN_API_KEY"):
        print("[Evals] LANGCHAIN_API_KEY not set — skipping LangSmith evals.")
        print("[Evals] Set LANGCHAIN_API_KEY in .env to enable evals.")
        return

    client = Client()
    dataset_name = build_dev_agent_dataset(client)

    from agents.client import get_llm
    from agents import dev_agent
    from langchain_core.runnables import RunnableLambda

    spec = Path("event-ledger-candidate-handout.md")
    spec_text = spec.read_text(encoding="utf-8") if spec.exists() else ""
    arch = Path("docs/architecture.md")
    arch_text = arch.read_text(encoding="utf-8") if arch.exists() else ""

    def run_agent(inputs: dict) -> dict:
        output = dev_agent.run(
            module=inputs["module"],
            spec_content=spec_text,
            architecture_content=arch_text,
            existing_code={},
        )
        combined = "\n\n".join(f.content for f in output.files)
        return {"content": combined}

    target = RunnableLambda(run_agent)

    results = evaluate(
        target,
        data=dataset_name,
        evaluators=[eval_syntax_valid, eval_no_placeholders],
        experiment_prefix="dev-agent",
        metadata={"model": "gpt-4o-mini", "provider": "github-models"},
    )

    print(f"\n[Evals] Dev Agent results:")
    for r in results:
        print(f"  {r}")


def run_all_evals() -> None:
    print("\n[Evals] Running LangSmith evaluations...\n")
    run_dev_agent_evals()
    print("\n[Evals] Done. View results at https://smith.langchain.com\n")


if __name__ == "__main__":
    run_all_evals()
