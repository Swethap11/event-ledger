"""
Phase 5 — Security Agent
Reviews all app/ code and produces reports/security-review.md
Run: python run_phase5.py
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

from ai_sdlc.agents import security_agent

APP_DIR = Path("app")


def collect_code() -> dict[str, str]:
    return {
        str(f): f.read_text(encoding="utf-8")
        for f in sorted(APP_DIR.rglob("*.py"))
        if f.stat().st_size > 0
    }


def main() -> None:
    if not APP_DIR.exists():
        raise FileNotFoundError("app/ directory not found. Run Phase 4 first.")

    code = collect_code()
    print(f"[Phase 5] Security Agent reviewing {len(code)} files...")

    output = security_agent.run(code)
    security_agent.save(output)

    print(f"\n[Phase 5] Done.")
    print(f"  Risk level : {output.risk_level}")
    print(f"  Findings   : {len(output.findings)}")
    print()

    for f in output.findings:
        print(f"  [{f.severity}] {f.file}")
        print(f"    Issue : {f.issue}")
        print(f"    Fix   : {f.recommendation}")
        print()

    print(f"  Full report: reports/security-review.md")

    high = [f for f in output.findings if f.severity == "HIGH"]
    if high:
        print(f"\n  WARNING: {len(high)} HIGH severity finding(s) — review before committing.")
    else:
        print(f"\n  Approved — no HIGH severity findings.")


if __name__ == "__main__":
    main()
