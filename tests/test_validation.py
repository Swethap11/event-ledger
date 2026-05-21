import pytest
from decimal import Decimal
from fastapi import status


@pytest.mark.parametrize(
    "payload, expected_status",
    [
        ({"eventId": "1", "accountId": "acc1", "type": "CREDIT", "amount": 0, "currency": "USD", "eventTimestamp": "2023-01-01T00:00:00Z"}, status.HTTP_422_UNPROCESSABLE_ENTITY),
        ({"eventId": "2", "accountId": "acc2", "type": "CREDIT", "amount": -100.00, "currency": "USD", "eventTimestamp": "2023-01-01T00:00:00Z"}, status.HTTP_422_UNPROCESSABLE_ENTITY),
        ({"eventId": "3", "accountId": "acc3", "type": "TRANSFER", "amount": 100.00, "currency": "USD", "eventTimestamp": "2023-01-01T00:00:00Z"}, status.HTTP_422_UNPROCESSABLE_ENTITY),
        ({"eventId": "4", "accountId": "acc4", "type": "CREDIT", "amount": 100.00, "currency": "USD", "eventTimestamp": "invalid_timestamp"}, status.HTTP_422_UNPROCESSABLE_ENTITY),
        ({"eventId": "5", "accountId": "acc5", "type": "CREDIT", "amount": 100.00, "currency": "USD", "eventTimestamp": "2023-01-01T00:00:00Z", "extraField": "extra"}, status.HTTP_422_UNPROCESSABLE_ENTITY),
    ],
)
def test_validation(client, payload, expected_status):
    response = client.post("/events", json=payload)
    assert response.status_code == expected_status


def test_unknown_event_id(client):
    response = client.get("/events/unknown_event_id")
    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert response.json() == {"detail": "Event 'unknown_event_id' not found"}
