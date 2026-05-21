import uuid


def _event(event_id, account_id, amount=100.0):
    return {
        "eventId": event_id,
        "accountId": account_id,
        "eventTimestamp": "2024-01-01T10:00:00Z",
        "type": "CREDIT",
        "amount": amount,
        "currency": "USD",
    }


def test_first_submission_returns_201(client):
    acct = f"acct-{uuid.uuid4().hex[:8]}"
    r = client.post("/events", json=_event(f"evt-{uuid.uuid4().hex[:8]}", acct))
    assert r.status_code == 201


def test_duplicate_returns_200(client):
    acct = f"acct-{uuid.uuid4().hex[:8]}"
    eid = f"evt-{uuid.uuid4().hex[:8]}"
    client.post("/events", json=_event(eid, acct))
    r = client.post("/events", json=_event(eid, acct))
    assert r.status_code == 200


def test_duplicate_does_not_change_balance(client):
    acct = f"acct-{uuid.uuid4().hex[:8]}"
    eid = f"evt-{uuid.uuid4().hex[:8]}"
    client.post("/events", json=_event(eid, acct, amount=100.0))
    client.post("/events", json=_event(eid, acct, amount=100.0))
    r = client.get(f"/accounts/{acct}/balance")
    assert r.status_code == 200
    assert float(r.json()["balance"]) == 100.0


def test_different_event_ids_both_create(client):
    acct = f"acct-{uuid.uuid4().hex[:8]}"
    r1 = client.post("/events", json=_event(f"evt-{uuid.uuid4().hex[:8]}", acct))
    r2 = client.post("/events", json=_event(f"evt-{uuid.uuid4().hex[:8]}", acct))
    assert r1.status_code == 201
    assert r2.status_code == 201
    r = client.get(f"/accounts/{acct}/balance")
    assert float(r.json()["balance"]) == 200.0
