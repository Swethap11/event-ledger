"""
Phase 7 — Docs Agent + Changelog Agent
Generates: docs/api-guide.md, CHANGELOG.md
Run: python run_phase7.py
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

from ai_sdlc.agents import changelog_agent, docs_agent
from ai_sdlc.validators.server_validator import start_server, stop_server

import time
import httpx

SPEC_PATH = Path("docs/project/handout.md")


def main() -> None:
    spec = SPEC_PATH.read_text(encoding="utf-8")[:2000]

    # --- Changelog Agent (no server needed) ---
    print("[Phase 7] Changelog Agent...")
    git_log = changelog_agent.get_git_log()
    changelog_out = changelog_agent.run(git_log)
    changelog_agent.save(changelog_out)

    # --- Docs Agent (needs live OpenAPI spec) ---
    print("[Phase 7] Starting server for OpenAPI spec...")
    proc = start_server()
    time.sleep(4)

    try:
        r = httpx.get("http://localhost:8000/openapi.json", timeout=5)
        r.raise_for_status()
        openapi_spec = r.json()
        print("[Phase 7] OpenAPI spec fetched.")
    except Exception as e:
        stop_server(proc)
        raise RuntimeError(f"Could not fetch OpenAPI spec: {e}")
    finally:
        stop_server(proc)

    print("[Phase 7] Docs Agent generating api-guide.md...")
    docs_out = docs_agent.run(openapi_spec, spec)
    docs_agent.save(docs_out)

    print("\n[Phase 7] Done.")
    print("  docs/api-guide.md")
    print("  CHANGELOG.md")


if __name__ == "__main__":
    main()
