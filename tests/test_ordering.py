import uuid


def test_balance_correct_regardless_of_submission_order(client):
    acct = f"acct-{uuid.uuid4().hex[:8]}"
    client.post("/events", json={
        "eventId": f"e-{uuid.uuid4().hex[:8]}", "accountId": acct,
        "type": "CREDIT", "amount": 50.0, "currency": "USD",
        "eventTimestamp": "2024-01-01T11:00:00Z",
    })
    client.post("/events", json={
        "eventId": f"e-{uuid.uuid4().hex[:8]}", "accountId": acct,
        "type": "CREDIT", "amount": 100.0, "currency": "USD",
        "eventTimestamp": "2024-01-01T09:00:00Z",
    })
    r = client.get(f"/accounts/{acct}/balance")
    assert r.status_code == 200
    assert float(r.json()["balance"]) == 150.0


def test_events_returned_in_chronological_order(client):
    acct = f"acct-{uuid.uuid4().hex[:8]}"
    client.post("/events", json={
        "eventId": f"e-{uuid.uuid4().hex[:8]}", "accountId": acct,
        "type": "CREDIT", "amount": 10.0, "currency": "USD",
        "eventTimestamp": "2024-03-01T00:00:00Z",
    })
    client.post("/events", json={
        "eventId": f"e-{uuid.uuid4().hex[:8]}", "accountId": acct,
        "type": "CREDIT", "amount": 20.0, "currency": "USD",
        "eventTimestamp": "2024-01-01T00:00:00Z",
    })
    client.post("/events", json={
        "eventId": f"e-{uuid.uuid4().hex[:8]}", "accountId": acct,
        "type": "CREDIT", "amount": 30.0, "currency": "USD",
        "eventTimestamp": "2024-02-01T00:00:00Z",
    })
    r = client.get(f"/events?account={acct}")
    assert r.status_code == 200
    timestamps = [e["eventTimestamp"] for e in r.json()]
    assert timestamps == sorted(timestamps)
