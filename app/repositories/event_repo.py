import json
from datetime import datetime
from decimal import Decimal

from sqlmodel import Session, func, select

from app.models.orm import AuditLog, Event
from app.models.schemas import EventCreate


class EventRepository:
    def __init__(self, session: Session):
        self.session = session

    def get_by_id(self, event_id: str) -> Event | None:
        return self.session.get(Event, event_id)

    def get_by_account(self, account_id: str) -> list[Event]:
        statement = (
            select(Event)
            .where(Event.account_id == account_id)
            .order_by(Event.event_timestamp.asc())
        )
        return self.session.exec(statement).all()

    def create(self, payload: EventCreate) -> Event:
        event = Event(
            event_id=payload.eventId,
            account_id=payload.accountId,
            type=payload.type.value,
            amount=payload.amount,
            currency=payload.currency,
            event_timestamp=payload.eventTimestamp,
            metadata_json=json.dumps(payload.metadata) if payload.metadata else None,
            received_at=datetime.utcnow(),
        )
        self.session.add(event)
        self.session.commit()
        self.session.refresh(event)
        return event

    def get_balance(self, account_id: str) -> tuple[Decimal, str | None]:
        credit_sum = (
            self.session.scalar(
                select(func.sum(Event.amount)).where(
                    Event.account_id == account_id, Event.type == "CREDIT"
                )
            )
            or Decimal("0")
        )
        debit_sum = (
            self.session.scalar(
                select(func.sum(Event.amount)).where(
                    Event.account_id == account_id, Event.type == "DEBIT"
                )
            )
            or Decimal("0")
        )
        events = self.session.exec(
            select(Event).where(Event.account_id == account_id).limit(1)
        ).all()
        currency = events[0].currency if events else None
        return Decimal(credit_sum) - Decimal(debit_sum), currency

    def account_exists(self, account_id: str) -> bool:
        statement = select(Event).where(Event.account_id == account_id).limit(1)
        return self.session.exec(statement).first() is not None

    def write_audit(
        self,
        endpoint: str,
        status_code: int,
        outcome: str,
        event_id: str | None,
        account_id: str | None,
        ip: str | None,
    ) -> None:
        audit_log = AuditLog(
            endpoint=endpoint,
            status_code=status_code,
            outcome=outcome,
            event_id=event_id,
            account_id=account_id,
            ip_address=ip,
        )
        self.session.add(audit_log)
        self.session.commit()
