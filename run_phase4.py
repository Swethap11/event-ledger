"""
Phase 4 — Dev Agent: services, routes, main
Generates: app/services/, app/routes/, app/main.py
Runs: syntax + lint + server start + contract validation
Run: python run_phase4.py
"""

import os
import subprocess
from pathlib import Path


def _load_dotenv() -> None:
    env_file = Path(".env")
    if not env_file.exists():
        return
    for line in env_file.read_text(encoding="utf-8").splitlines():
        if "=" in line and not line.startswith("#"):
            k, v = line.split("=", 1)
            os.environ.setdefault(k.strip(), v.strip())


def _github_token_from_gh() -> str | None:
    try:
        result = subprocess.run(
            ["gh", "auth", "token"], capture_output=True, text=True, check=True
        )
        return result.stdout.strip() or None
    except (FileNotFoundError, subprocess.CalledProcessError):
        return None


_load_dotenv()
if not os.environ.get("GITHUB_TOKEN"):
    token = _github_token_from_gh()
    if token:
        os.environ["GITHUB_TOKEN"] = token

if not os.environ.get("GITHUB_TOKEN"):
    raise EnvironmentError("GITHUB_TOKEN not set. Add it to .env")

from agents import dev_agent
from validators.syntax_validator import validate_syntax
from validators.lint_validator import validate_lint
from validators.server_validator import validate_server_and_contract
from validators.contract_validator import validate_contract

SPEC_PATH = Path("event-ledger-candidate-handout.md")
ARCH_PATH = Path("docs/architecture.md")
MODULES = ["services", "routes", "main"]
MAX_RETRIES = 3


def collect_existing() -> dict[str, str]:
    code: dict[str, str] = {}
    app_dir = Path("app")
    if app_dir.exists():
        for f in sorted(app_dir.rglob("*.py")):
            code[str(f)] = f.read_text(encoding="utf-8")
    return code


def run_validators(module: str) -> tuple[bool, str]:
    errors: list[str] = []

    for py_file in sorted(Path("app").rglob("*.py")):
        ok, err = validate_syntax(py_file)
        if not ok:
            errors.append(f"Syntax [{py_file}]: {err}")
        ok, err = validate_lint(py_file)
        if not ok:
            errors.append(f"Lint [{py_file}]: {err}")

    if errors:
        return False, "\n".join(errors)

    if module == "main":
        print("  Starting server for contract validation...")
        ok, err = validate_server_and_contract(validate_contract)
        if not ok:
            return False, err
        print("  Server and contract validation passed.")

    return True, ""


def main() -> None:
    spec = SPEC_PATH.read_text(encoding="utf-8")
    arch = ARCH_PATH.read_text(encoding="utf-8") if ARCH_PATH.exists() else ""
    existing_code = collect_existing()

    for module in MODULES:
        print(f"\n[Phase 4] Dev Agent → module: {module}")
        feedback = ""
        success = False

        for attempt in range(1, MAX_RETRIES + 1):
            print(f"  Attempt {attempt}/{MAX_RETRIES}...")
            output = dev_agent.run(module, spec, arch, existing_code, feedback)
            saved = dev_agent.save(output)
            existing_code.update(saved)

            ok, err = run_validators(module)
            if ok:
                print(f"  Validators passed.")
                print(f"  Summary: {output.summary}")
                success = True
                break
            else:
                print(f"  Validators failed — retrying with feedback...")
                print(err[:300])
                feedback = err

        if not success:
            print(f"\n[Phase 4] FAILED on module '{module}' after {MAX_RETRIES} attempts.")
            raise SystemExit(1)

    print("\n[Phase 4] Done. Full app generated and validated.")
    print("\nAll files:")
    for f in sorted(Path("app").rglob("*.py")):
        print(f"  {f}")
    print("\nTry it: uv run uvicorn app.main:app --reload")
    print("Docs  : http://localhost:8000/docs")


if __name__ == "__main__":
    main()
