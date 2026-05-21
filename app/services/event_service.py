import json

from sqlalchemy.exc import IntegrityError
from sqlmodel import Session

from app.core.exceptions import AccountNotFoundError, EventNotFoundError
from app.models.orm import Event
from app.models.schemas import BalanceResponse, EventCreate, EventResponse, EventType
from app.repositories.event_repo import EventRepository


def _orm_to_response(event: Event) -> EventResponse:
    metadata = None
    if event.metadata_json:
        metadata = json.loads(event.metadata_json)
    return EventResponse(
        eventId=event.event_id,
        accountId=event.account_id,
        type=EventType(event.type),
        amount=event.amount,
        currency=event.currency,
        eventTimestamp=event.event_timestamp,
        metadata=metadata,
        receivedAt=event.received_at,
    )


class EventService:
    def __init__(self, session: Session):
        self.repo = EventRepository(session)

    def submit(
        self, payload: EventCreate, ip: str | None = None
    ) -> tuple[EventResponse, bool]:
        try:
            event = self.repo.create(payload)
            self.repo.write_audit(
                endpoint="POST /events",
                status_code=201,
                outcome="CREATED",
                event_id=event.event_id,
                account_id=event.account_id,
                ip=ip,
            )
            return _orm_to_response(event), True
        except IntegrityError:
            self.repo.session.rollback()
            existing = self.repo.get_by_id(payload.eventId)
            self.repo.write_audit(
                endpoint="POST /events",
                status_code=200,
                outcome="DUPLICATE",
                event_id=existing.event_id,
                account_id=existing.account_id,
                ip=ip,
            )
            return _orm_to_response(existing), False

    def get_by_id(self, event_id: str, ip: str | None = None) -> EventResponse:
        event = self.repo.get_by_id(event_id)
        if not event:
            raise EventNotFoundError(event_id)
        self.repo.write_audit(
            endpoint="GET /events/{event_id}",
            status_code=200,
            outcome="FETCHED",
            event_id=event.event_id,
            account_id=event.account_id,
            ip=ip,
        )
        return _orm_to_response(event)

    def list_by_account(self, account_id: str) -> list[EventResponse]:
        events = self.repo.get_by_account(account_id)
        return [_orm_to_response(event) for event in events]

    def get_balance(self, account_id: str) -> BalanceResponse:
        if not self.repo.account_exists(account_id):
            raise AccountNotFoundError(account_id)
        balance, currency = self.repo.get_balance(account_id)
        return BalanceResponse(accountId=account_id, balance=balance, currency=currency)
