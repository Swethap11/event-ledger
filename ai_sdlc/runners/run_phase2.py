"""
Phase 2 — Design Agent
Reads the spec, produces docs/generated/architecture.md with a Mermaid diagram.
Run: python run_phase2.py
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
            ["gh", "auth", "token"],
            capture_output=True,
            text=True,
            check=True,
        )
    except (FileNotFoundError, subprocess.CalledProcessError):
        return None
    token = result.stdout.strip()
    return token or None


_load_dotenv()
if not os.environ.get("GITHUB_TOKEN"):
    gh_token = _github_token_from_gh()
    if gh_token:
        os.environ["GITHUB_TOKEN"] = gh_token

if not os.environ.get("GITHUB_TOKEN"):
    raise EnvironmentError(
        "GITHUB_TOKEN not set.\n"
        "Add it to your .env file:\n"
        "  GITHUB_TOKEN=your_token_here\n"
        "Get one at: github.com → Settings → Developer settings → Personal access tokens"
    )

from ai_sdlc.agents import design_agent

SPEC_CANDIDATES = [
    Path("docs/project/handout.md"),
    Path(r"C:\Users\nprat\Desktop\event-ledger\docs\project\handout.md"),
]

spec = None
for p in SPEC_CANDIDATES:
    if p.exists():
        spec = p.read_text(encoding="utf-8")
        print(f"[Phase 2] Spec loaded from: {p}")
        break

if spec is None:
    raise FileNotFoundError(
        "Spec file not found. Copy event-ledger-candidate-handout.md to the project root."
    )

print("[Phase 2] Running Design Agent via GitHub Models...")
output = design_agent.run(spec)
design_agent.save(output)

print("\n[Phase 2] Done.")
print(f"  Summary     : {output.summary}")
print(f"  Components  : {len(output.components)}")
print(f"  Decisions   : {len(output.design_decisions)}")
print(f"  Output file : docs/generated/architecture.md")
