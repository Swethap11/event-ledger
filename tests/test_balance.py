import uuid


def _event(event_id, account_id, amount, etype="CREDIT"):
    return {
        "eventId": event_id,
        "accountId": account_id,
        "eventTimestamp": "2024-01-01T10:00:00Z",
        "type": etype,
        "amount": amount,
        "currency": "USD",
    }


def test_credits_only(client):
    acct = f"acct-{uuid.uuid4().hex[:8]}"
    client.post("/events", json=_event(f"e-{uuid.uuid4().hex[:8]}", acct, 100.0))
    client.post("/events", json=_event(f"e-{uuid.uuid4().hex[:8]}", acct, 50.0))
    r = client.get(f"/accounts/{acct}/balance")
    assert r.status_code == 200
    assert float(r.json()["balance"]) == 150.0


def test_debits_only(client):
    acct = f"acct-{uuid.uuid4().hex[:8]}"
    client.post("/events", json=_event(f"e-{uuid.uuid4().hex[:8]}", acct, 80.0, "DEBIT"))
    r = client.get(f"/accounts/{acct}/balance")
    assert r.status_code == 200
    assert float(r.json()["balance"]) == -80.0


def test_mixed_credits_and_debits(client):
    acct = f"acct-{uuid.uuid4().hex[:8]}"
    client.post("/events", json=_event(f"e-{uuid.uuid4().hex[:8]}", acct, 200.0, "CREDIT"))
    client.post("/events", json=_event(f"e-{uuid.uuid4().hex[:8]}", acct, 75.0, "DEBIT"))
    r = client.get(f"/accounts/{acct}/balance")
    assert r.status_code == 200
    assert float(r.json()["balance"]) == 125.0


def test_unknown_account_returns_404(client):
    r = client.get("/accounts/acct-does-not-exist-xyz/balance")
    assert r.status_code == 404
