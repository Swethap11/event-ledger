"""
Event Ledger MCP Server
Exposes the ledger API as AI-callable tools.

Usage:
    uv run python mcp_server.py

Claude Desktop config (~/.claude/claude_desktop_config.json):
    {
      "mcpServers": {
        "event-ledger": {
          "command": "uv",
          "args": ["run", "python", "mcp_server.py"],
          "cwd": "/path/to/event-ledger"
        }
      }
    }

Requires the FastAPI server to be running at http://localhost:8000.
"""

import httpx
from mcp.server.fastmcp import FastMCP

BASE_URL = "http://localhost:8000"

mcp = FastMCP("event-ledger")


def _client() -> httpx.Client:
    return httpx.Client(base_url=BASE_URL, timeout=10)


@mcp.tool()
def submit_event(
    event_id: str,
    account_id: str,
    event_type: str,
    amount: float,
    currency: str,
    event_timestamp: str,
) -> dict:
    """Submit a financial event to the ledger.

    Returns the event record. Status 201 = created, 200 = duplicate (idempotent).
    event_type must be 'CREDIT' or 'DEBIT'. amount must be > 0.
    event_timestamp must be ISO 8601 (e.g. '2026-05-15T10:00:00Z').
    """
    with _client() as client:
        r = client.post("/events", json={
            "eventId": event_id,
            "accountId": account_id,
            "type": event_type,
            "amount": amount,
            "currency": currency,
            "eventTimestamp": event_timestamp,
        })
        return {"status": r.status_code, "body": r.json()}


@mcp.tool()
def get_event(event_id: str) -> dict:
    """Retrieve a single event by its ID."""
    with _client() as client:
        r = client.get(f"/events/{event_id}")
        return {"status": r.status_code, "body": r.json()}


@mcp.tool()
def list_events(account_id: str) -> dict:
    """List all events for an account, ordered chronologically by event timestamp."""
    with _client() as client:
        r = client.get("/events", params={"account": account_id})
        return {"status": r.status_code, "body": r.json()}


@mcp.tool()
def get_balance(account_id: str) -> dict:
    """Get the current net balance for an account (sum of CREDITs minus DEBITs).

    Returns 404 if the account has no events.
    """
    with _client() as client:
        r = client.get(f"/accounts/{account_id}/balance")
        return {"status": r.status_code, "body": r.json()}


@mcp.tool()
def health_check() -> dict:
    """Check if the Event Ledger API is running."""
    with _client() as client:
        r = client.get("/health")
        return {"status": r.status_code, "body": r.json()}


if __name__ == "__main__":
    mcp.run()
