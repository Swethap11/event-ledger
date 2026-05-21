import json
import traceback
from datetime import datetime, timezone
from pathlib import Path

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

ERROR_LOG = Path("logs/errors.jsonl")


class ErrorCaptureMiddleware(BaseHTTPMiddleware):
    """Captures 5xx responses and unhandled exceptions to logs/errors.jsonl."""

    async def dispatch(self, request: Request, call_next) -> Response:
        try:
            response = await call_next(request)
            if response.status_code >= 500:
                _write_event(
                    level="ERROR",
                    path=request.url.path,
                    method=request.method,
                    status_code=response.status_code,
                    message=f"HTTP {response.status_code} on {request.method} {request.url.path}",
                )
            return response
        except Exception as exc:
            tb = traceback.format_exc()
            _write_event(
                level="EXCEPTION",
                path=request.url.path,
                method=request.method,
                status_code=500,
                message=str(exc),
                traceback=tb,
            )
            raise


def _write_event(
    level: str,
    path: str,
    method: str,
    status_code: int,
    message: str,
    traceback: str = "",
) -> None:
    ERROR_LOG.parent.mkdir(parents=True, exist_ok=True)
    entry = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "level": level,
        "method": method,
        "path": path,
        "status_code": status_code,
        "message": message,
        "traceback": traceback,
        "resolved": False,
    }
    with ERROR_LOG.open("a", encoding="utf-8") as f:
        f.write(json.dumps(entry) + "\n")
