"""
Event Ledger — AI Agent Pipeline
Run: python agents/pipeline.py
"""

import os
import sys
import time
from pathlib import Path
# Load .env if present
env_file = Path(".env")
if env_file.exists():
    for line in env_file.read_text().splitlines():
        if "=" in line and not line.startswith("#"):
            k, v = line.split("=", 1)
            os.environ.setdefault(k.strip(), v.strip())

from agents import design_agent, dev_agent, security_agent, qa_agent, docs_agent, changelog_agent
from agents.guardrails import get_callbacks
from agents.evals import run_all_evals
from validators.syntax_validator import validate_syntax
from validators.lint_validator import validate_lint
from validators.server_validator import validate_server
from validators.contract_validator import validate_contract

SPEC_PATH = Path("event-ledger-candidate-handout.md")
MAX_RETRIES = 3
DEV_MODULES = ["core", "models", "repositories", "services", "routes", "main"]


def load_spec() -> str:
    candidates = [
        Path("event-ledger-candidate-handout.md"),
        Path(r"C:\Users\nprat\Downloads\event-ledger-candidate-handout.md"),
    ]
    for p in candidates:
        if p.exists():
            return p.read_text(encoding="utf-8")
    raise FileNotFoundError("Spec file not found. Place event-ledger-candidate-handout.md in the project root.")


def collect_app_code() -> dict[str, str]:
    code: dict[str, str] = {}
    app_dir = Path("app")
    if app_dir.exists():
        for f in sorted(app_dir.rglob("*.py")):
            code[str(f)] = f.read_text(encoding="utf-8")
    return code


def run_validators(module: str) -> tuple[bool, str]:
    errors: list[str] = []

    app_dir = Path("app")
    for py_file in app_dir.rglob("*.py"):
        ok, err = validate_syntax(py_file)
        if not ok:
            errors.append(f"Syntax error in {py_file}: {err}")

        ok, err = validate_lint(py_file)
        if not ok:
            errors.append(f"Lint error in {py_file}: {err}")

    if errors:
        return False, "\n".join(errors)

    if module in ("routes", "main"):
        ok, err = validate_server()
        if not ok:
            errors.append(f"Server failed to start: {err}")
            return False, "\n".join(errors)

        ok, errs = validate_contract()
        if not ok:
            errors.extend(errs)
            return False, "\n".join(errors)

    return True, ""


def print_summary(start: float, token_counts: dict[str, int]) -> None:
    elapsed = time.time() - start
    total = sum(token_counts.values())
    print("\n" + "=" * 60)
    print("  PIPELINE COMPLETE")
    print("=" * 60)
    print(f"  Total time : {elapsed:.1f}s")
    print(f"  Total calls: {total} LLM interactions")
    for agent, count in token_counts.items():
        print(f"    {agent:<20} {count} calls")
    langsmith_proj = os.environ.get("LANGCHAIN_PROJECT", "event-ledger")
    if os.environ.get("LANGCHAIN_TRACING_V2") == "true":
        print(f"\n  LangSmith trace: https://smith.langchain.com/projects/{langsmith_proj}")
    print("=" * 60)


def main() -> None:
    start = time.time()
    token_counts: dict[str, int] = {}
    print("\n[Pipeline] Starting Event Ledger AI Agent Pipeline\n")

    spec = load_spec()
    print(f"[Pipeline] Spec loaded ({len(spec)} chars)\n")

    # Phase 1 — Design Agent
    print("[Pipeline] Running Design Agent...")
    design_out = design_agent.run(spec)
    design_agent.save(design_out)
    arch_content = Path("docs/architecture.md").read_text(encoding="utf-8")
    token_counts["design_agent"] = 1
    print("[Pipeline] Design Agent done.\n")

    # Phase 2 — Dev Agent (module by module with validation loop)
    existing_code: dict[str, str] = {}
    for module in DEV_MODULES:
        print(f"[Pipeline] Dev Agent → module: {module}")
        feedback = ""
        success = False

        for attempt in range(1, MAX_RETRIES + 1):
            print(f"  Attempt {attempt}/{MAX_RETRIES}...")
            output = dev_agent.run(module, spec, arch_content, existing_code, feedback)
            saved = dev_agent.save(output)
            existing_code.update(saved)
            token_counts[f"dev_agent_{module}"] = attempt

            ok, err = run_validators(module)
            if ok:
                print(f"  [Validators] Passed for module: {module}")
                success = True
                break
            else:
                print(f"  [Validators] Failed — feeding back to agent:\n  {err[:200]}...")
                feedback = err

        if not success:
            print(f"[Pipeline] FAILED: module '{module}' did not pass validation after {MAX_RETRIES} attempts.")
            print("[Pipeline] Stopping — human review required.")
            sys.exit(1)

        print(f"[Pipeline] Module '{module}' complete.\n")

    # Phase 3 — Security Agent
    print("[Pipeline] Running Security Agent...")
    app_code = collect_app_code()
    sec_out = security_agent.run(app_code)
    security_agent.save(sec_out)
    token_counts["security_agent"] = 1
    if not sec_out.approved:
        print("[Pipeline] WARNING: Security Agent flagged HIGH severity issues. Review reports/security-review.md.")
    print("[Pipeline] Security Agent done.\n")

    # Phase 4 — QA Agent
    print("[Pipeline] Running QA Agent...")
    qa_out = qa_agent.run(app_code, spec)
    qa_agent.save(qa_out)
    token_counts["qa_agent"] = 1
    passed, _ = qa_agent.run_tests_and_report()
    if not passed:
        print("[Pipeline] WARNING: Some tests failed. Review reports/coverage.md.")
    print("[Pipeline] QA Agent done.\n")

    # Phase 5 — Docs Agent (needs running server)
    print("[Pipeline] Running Docs Agent (starting server to fetch OpenAPI spec)...")
    ok, err = validate_server()
    if ok:
        try:
            import httpx
            spec_json = httpx.get("http://localhost:8000/openapi.json", timeout=5).json()
            docs_out = docs_agent.run(spec_json, spec)
            docs_agent.save(docs_out)
            token_counts["docs_agent"] = 1
            print("[Pipeline] Docs Agent done.\n")
        except Exception as e:
            print(f"[Pipeline] Docs Agent skipped — {e}\n")
    else:
        print(f"[Pipeline] Docs Agent skipped — server not available: {err}\n")

    # Phase 6 — Changelog Agent
    print("[Pipeline] Running Changelog Agent...")
    git_log = changelog_agent.get_git_log()
    ch_out = changelog_agent.run(git_log)
    changelog_agent.save(ch_out)
    token_counts["changelog_agent"] = 1
    print("[Pipeline] Changelog Agent done.\n")

    # Phase 7 — LangSmith Evals
    print("[Pipeline] Running LangSmith evaluations...")
    run_all_evals()

    print_summary(start, token_counts)


if __name__ == "__main__":
    main()
