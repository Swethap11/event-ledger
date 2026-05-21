import subprocess
import time
import signal
import httpx
from pathlib import Path

SERVER_PORT = 8000
HEALTH_URL = f"http://localhost:{SERVER_PORT}/health"
STARTUP_WAIT = 4


def validate_server() -> tuple[bool, str]:
    proc = subprocess.Popen(
        ["python", "-m", "uvicorn", "app.main:app", "--port", str(SERVER_PORT), "--log-level", "error"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    time.sleep(STARTUP_WAIT)

    try:
        r = httpx.get(HEALTH_URL, timeout=5)
        proc.terminate()
        proc.wait(timeout=5)
        if r.status_code == 200:
            return True, ""
        return False, f"Health check returned HTTP {r.status_code}"
    except httpx.ConnectError:
        stderr = proc.stderr.read().decode(errors="replace") if proc.stderr else ""
        proc.terminate()
        proc.wait(timeout=5)
        return False, f"Server did not start. stderr: {stderr[:500]}"
    except Exception as e:
        proc.terminate()
        proc.wait(timeout=5)
        return False, str(e)
