import httpx

BASE_URL = "http://localhost:8000"

VALID_EVENT = {
    "eventId": "contract-test-001",
    "accountId": "acct-contract-test",
    "type": "CREDIT",
    "amount": 100.00,
    "currency": "USD",
    "eventTimestamp": "2026-05-15T10:00:00Z",
}


def validate_contract(base_url: str = BASE_URL) -> tuple[bool, list[str]]:
    errors: list[str] = []

    with httpx.Client(base_url=base_url, timeout=10) as client:

        # POST /events — 201 on first submit
        r = client.post("/events", json=VALID_EVENT)
        if r.status_code != 201:
            errors.append(f"POST /events expected 201, got {r.status_code}: {r.text[:200]}")
        else:
            body = r.json()
            for field in ("eventId", "accountId", "type", "amount", "currency", "eventTimestamp"):
                if field not in body:
                    errors.append(f"POST /events response missing field: {field}")

        # POST /events — 200 on duplicate (idempotency)
        r = client.post("/events", json=VALID_EVENT)
        if r.status_code != 200:
            errors.append(f"POST /events duplicate expected 200, got {r.status_code}")

        # GET /events/{id}
        r = client.get(f"/events/{VALID_EVENT['eventId']}")
        if r.status_code != 200:
            errors.append(f"GET /events/{{id}} expected 200, got {r.status_code}")

        # GET /events/{id} — 404 for unknown
        r = client.get("/events/does-not-exist-xyz")
        if r.status_code != 404:
            errors.append(f"GET /events/unknown expected 404, got {r.status_code}")

        # GET /events?account=
        r = client.get("/events", params={"account": VALID_EVENT["accountId"]})
        if r.status_code != 200:
            errors.append(f"GET /events?account= expected 200, got {r.status_code}")
        elif not isinstance(r.json(), list):
            errors.append("GET /events?account= should return a list")

        # GET /accounts/{id}/balance
        r = client.get(f"/accounts/{VALID_EVENT['accountId']}/balance")
        if r.status_code != 200:
            errors.append(f"GET /accounts/{{id}}/balance expected 200, got {r.status_code}")
        else:
            body = r.json()
            if "balance" not in body:
                errors.append("GET /accounts/{id}/balance response missing 'balance' field")
            if abs(body.get("balance", 0) - 100.0) > 0.001:
                errors.append(f"Balance expected 100.0, got {body.get('balance')}")

        # GET /accounts/{id}/balance — 404 for unknown account
        r = client.get("/accounts/acct-unknown-xyz/balance")
        if r.status_code != 404:
            errors.append(f"GET /accounts/unknown/balance expected 404, got {r.status_code}")

        # POST /events — validation: zero amount
        r = client.post("/events", json={**VALID_EVENT, "eventId": "val-001", "amount": 0})
        if r.status_code not in (400, 422):
            errors.append(f"POST /events zero amount expected 422, got {r.status_code}")

        # POST /events — validation: bad type
        r = client.post("/events", json={**VALID_EVENT, "eventId": "val-002", "type": "TRANSFER"})
        if r.status_code not in (400, 422):
            errors.append(f"POST /events bad type expected 422, got {r.status_code}")

    return len(errors) == 0, errors
