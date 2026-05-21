from datetime import datetime

from sqlmodel import Column, DateTime, Field, SQLModel


class Event(SQLModel, table=True):
    __tablename__ = "events"
    event_id: str = Field(primary_key=True)
    account_id: str = Field(index=True, nullable=False)
    type: str = Field(nullable=False)  # "CREDIT" or "DEBIT"
    amount: float = Field(nullable=False)
    currency: str = Field(nullable=False)
    event_timestamp: datetime = Field(
        sa_column=Column(DateTime(timezone=True), nullable=False, index=True)
    )
    metadata_json: str | None = Field(default=None)  # JSON serialised dict
    received_at: datetime = Field(default_factory=datetime.utcnow)


class AuditLog(SQLModel, table=True):
    __tablename__ = "audit_log"
    id: int | None = Field(default=None, primary_key=True)
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    endpoint: str  # e.g. "POST /events"
    event_id: str | None = Field(default=None)
    account_id: str | None = Field(default=None)
    status_code: int
    outcome: str  # "CREATED", "DUPLICATE", "REJECTED", "ERROR", "FETCHED"
