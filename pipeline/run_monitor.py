"""
Agentic production monitor.

Watches logs/errors.jsonl for unresolved 5xx events.
For each new error:
  1. Loads the affected source files
  2. Calls monitor_agent to classify and generate a fix
  3. Applies the fix (BUG) or logs the finding (SECURITY/TEST_GAP)
  4. Marks the error as resolved
  5. Restarts the FastAPI server if a fix was applied

Usage:
    uv run python pipeline/run_monitor.py

Requires OPENAI_API_KEY in environment.
Requires the FastAPI server to be running (started separately).
"""

import json
import os
import signal
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

# Resolve project root (one level up from pipeline/)
ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))
os.chdir(ROOT)

from agents import monitor_agent

ERROR_LOG = ROOT / "logs" / "errors.jsonl"
REPORTS_DIR = ROOT / "reports" / "monitor"
APP_FILES = list((ROOT / "app").rglob("*.py"))

POLL_INTERVAL = 10  # seconds between log checks
_server_process: subprocess.Popen | None = None


# ---------------------------------------------------------------------------
# Server lifecycle
# ---------------------------------------------------------------------------

def start_server() -> subprocess.Popen:
    print("[Monitor] Starting FastAPI server...")
    proc = subprocess.Popen(
        [sys.executable, "-m", "uvicorn", "app.main:app",
         "--host", "0.0.0.0", "--port", "8000"],
        cwd=ROOT,
    )
    time.sleep(3)
    print(f"[Monitor] Server PID {proc.pid}")
    return proc


def restart_server(proc: subprocess.Popen) -> subprocess.Popen:
    print("[Monitor] Restarting server after fix...")
    proc.send_signal(signal.SIGTERM)
    try:
        proc.wait(timeout=10)
    except subprocess.TimeoutExpired:
        proc.kill()
    return start_server()


# ---------------------------------------------------------------------------
# Error log helpers
# ---------------------------------------------------------------------------

def read_unresolved() -> list[tuple[int, dict]]:
    if not ERROR_LOG.exists():
        return []
    entries = []
    lines = ERROR_LOG.read_text(encoding="utf-8").splitlines()
    for i, line in enumerate(lines):
        try:
            event = json.loads(line)
            if not event.get("resolved"):
                entries.append((i, event))
        except json.JSONDecodeError:
            continue
    return entries


def mark_resolved(line_index: int) -> None:
    lines = ERROR_LOG.read_text(encoding="utf-8").splitlines()
    event = json.loads(lines[line_index])
    event["resolved"] = True
    event["resolved_at"] = datetime.now(timezone.utc).isoformat()
    lines[line_index] = json.dumps(event)
    ERROR_LOG.write_text("\n".join(lines) + "\n", encoding="utf-8")


# ---------------------------------------------------------------------------
# Source file resolution
# ---------------------------------------------------------------------------

def _load_app_files(affected_file: str) -> dict[str, str]:
    """Load the affected file + its immediate module siblings."""
    target = ROOT / affected_file
    sources: dict[str, str] = {}
    if target.exists():
        sources[affected_file] = target.read_text(encoding="utf-8")
    # Always include exceptions and schemas — agents frequently need them
    for extra in ["app/core/exceptions.py", "app/models/schemas.py"]:
        p = ROOT / extra
        if p.exists() and extra not in sources:
            sources[extra] = p.read_text(encoding="utf-8")
    return sources


# ---------------------------------------------------------------------------
# Fix application
# ---------------------------------------------------------------------------

def apply_fix(output: monitor_agent.MonitorOutput) -> bool:
    if not output.fix or output.classification == "TRANSIENT":
        return False
    target = ROOT / output.affected_file
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(output.fix, encoding="utf-8")
    print(f"[Monitor] Fix applied → {output.affected_file}")
    return True


def save_report(event: dict, output: monitor_agent.MonitorOutput) -> None:
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S")
    report_path = REPORTS_DIR / f"incident-{ts}.md"
    report_path.write_text(
        f"# Incident Report — {ts}\n\n"
        f"## Error\n```json\n{json.dumps(event, indent=2)}\n```\n\n"
        f"## Classification\n{output.classification} / {output.severity}\n\n"
        f"## Root Cause\n{output.root_cause}\n\n"
        f"## Fix\n{output.fix_description}\n\n"
        f"**Confidence:** {output.confidence:.0%}\n",
        encoding="utf-8",
    )
    print(f"[Monitor] Incident report → {report_path.name}")


# ---------------------------------------------------------------------------
# Main loop
# ---------------------------------------------------------------------------

def process_error(line_index: int, event: dict) -> bool:
    """Returns True if a fix was applied (server should restart)."""
    print(f"\n[Monitor] Error detected: {event['method']} {event['path']} "
          f"({event['status_code']}) — {event['message'][:80]}")

    source_files = _load_app_files(event.get("affected_file", ""))
    # Fallback: load all app files if no specific file is known
    if not source_files:
        source_files = {
            str(p.relative_to(ROOT)): p.read_text(encoding="utf-8")
            for p in APP_FILES
        }

    try:
        output = monitor_agent.run(event, source_files)
    except Exception as e:
        print(f"[Monitor] Agent call failed: {e}")
        mark_resolved(line_index)
        return False

    print(f"[Monitor] Classification: {output.classification} | "
          f"Severity: {output.severity} | Confidence: {output.confidence:.0%}")
    print(f"[Monitor] Root cause: {output.root_cause}")

    save_report(event, output)
    fixed = apply_fix(output)
    mark_resolved(line_index)
    return fixed


def main() -> None:
    global _server_process
    print("[Monitor] Agentic production monitor starting...")
    print(f"[Monitor] Watching: {ERROR_LOG}")
    print(f"[Monitor] Poll interval: {POLL_INTERVAL}s\n")

    _server_process = start_server()

    try:
        while True:
            unresolved = read_unresolved()
            for line_index, event in unresolved:
                should_restart = process_error(line_index, event)
                if should_restart and _server_process:
                    _server_process = restart_server(_server_process)
            time.sleep(POLL_INTERVAL)
    except KeyboardInterrupt:
        print("\n[Monitor] Shutting down...")
        if _server_process:
            _server_process.terminate()


if __name__ == "__main__":
    main()
