"""
Phase 3 — Dev Agent: core, models, repositories
Generates: app/core/, app/models/, app/repositories/
Run: python run_phase3.py
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

from ai_sdlc.agents import dev_agent
from ai_sdlc.validators.syntax_validator import validate_syntax
from ai_sdlc.validators.lint_validator import validate_lint

SPEC_PATH = Path("docs/project/handout.md")
ARCH_PATH = Path("docs/generated/architecture.md")
MODULES = ["core", "models", "repositories"]
MAX_RETRIES = 3


def run_validators(module: str) -> tuple[bool, str]:
    errors: list[str] = []
    app_dir = Path("app")
    if not app_dir.exists():
        return True, ""
    for py_file in sorted(app_dir.rglob("*.py")):
        ok, err = validate_syntax(py_file)
        if not ok:
            errors.append(f"Syntax [{py_file}]: {err}")
        ok, err = validate_lint(py_file)
        if not ok:
            errors.append(f"Lint [{py_file}]: {err}")
    return (len(errors) == 0), "\n".join(errors)


def main() -> None:
    spec = SPEC_PATH.read_text(encoding="utf-8")
    arch = ARCH_PATH.read_text(encoding="utf-8") if ARCH_PATH.exists() else ""
    existing_code: dict[str, str] = {}

    for module in MODULES:
        print(f"\n[Phase 3] Dev Agent → module: {module}")
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
                print(err)
                feedback = err

        if not success:
            print(f"\n[Phase 3] FAILED on module '{module}' after {MAX_RETRIES} attempts.")
            print("Review the errors above and adjust the prompt if needed.")
            raise SystemExit(1)

    print("\n[Phase 3] Done.")
    print("Generated files:")
    for f in sorted(Path("app").rglob("*.py")):
        print(f"  {f}")


if __name__ == "__main__":
    main()
