import subprocess
import sys
import time
from pathlib import Path

import httpx

SERVER_PORT = 8000
HEALTH_URL = f"http://localhost:{SERVER_PORT}/health"
STARTUP_WAIT = 4
PROJECT_ROOT = Path(__file__).resolve().parent.parent


def _uvicorn_cmd() -> list[str]:
    return [
        sys.executable,
        "-m",
        "uvicorn",
        "app.main:app",
        "--port",
        str(SERVER_PORT),
        "--log-level",
        "error",
    ]


def start_server() -> subprocess.Popen:
    return subprocess.Popen(
        _uvicorn_cmd(),
        cwd=PROJECT_ROOT,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )


def stop_server(proc: subprocess.Popen) -> None:
    if proc.poll() is None:
        proc.terminate()
        try:
            proc.wait(timeout=5)
        except subprocess.TimeoutExpired:
            proc.kill()
            proc.wait(timeout=5)


def validate_server() -> tuple[bool, str]:
    """Start uvicorn, hit /health, then stop."""
    proc = start_server()
    time.sleep(STARTUP_WAIT)

    try:
        r = httpx.get(HEALTH_URL, timeout=5)
        if r.status_code == 200:
            return True, ""
        return False, f"Health check returned HTTP {r.status_code}"
    except httpx.ConnectError:
        stderr = proc.stderr.read().decode(errors="replace") if proc.stderr else ""
        return False, f"Server did not start. stderr: {stderr[:500]}"
    except Exception as e:
        return False, str(e)
    finally:
        stop_server(proc)


def validate_server_and_contract(
    contract_fn,
) -> tuple[bool, str]:
    """Keep server running for contract checks, then shut down."""
    proc = start_server()
    time.sleep(STARTUP_WAIT)

    try:
        r = httpx.get(HEALTH_URL, timeout=5)
        if r.status_code != 200:
            return False, f"Health check returned HTTP {r.status_code}"

        ok, errs = contract_fn()
        if not ok:
            return False, "\n".join(errs)
        return True, ""
    except httpx.ConnectError:
        stderr = proc.stderr.read().decode(errors="replace") if proc.stderr else ""
        return False, f"Server did not start. stderr: {stderr[:500]}"
    except Exception as e:
        return False, str(e)
    finally:
        stop_server(proc)
