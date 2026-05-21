from datetime import datetime

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
            type=payload.type,
            amount=payload.amount,
            currency=payload.currency,
            event_timestamp=payload.eventTimestamp,
            metadata_json=payload.metadata,
            received_at=datetime.utcnow(),
        )
        self.session.add(event)
        self.session.commit()
        self.session.refresh(event)
        return event

    def get_balance(self, account_id: str) -> tuple[float, str | None]:
        credit_sum = (
            self.session.exec(
                select(func.sum(Event.amount)).where(
                    Event.account_id == account_id, Event.type == "CREDIT"
                )
            ).one()[0]
            or 0.0
        )
        debit_sum = (
            self.session.exec(
                select(func.sum(Event.amount)).where(
                    Event.account_id == account_id, Event.type == "DEBIT"
                )
            ).one()[0]
            or 0.0
        )
        balance = round(credit_sum - debit_sum, 10)
        return balance, "USD"  # Assuming currency is always USD for simplicity

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
            event_id=event_id,
            account_id=account_id,
            status_code=status_code,
            outcome=outcome,
        )
        self.session.add(audit_log)
        self.session.commit()
