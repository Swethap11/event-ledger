from datetime import datetime
from enum import StrEnum
from typing import Annotated, Any

from pydantic import BaseModel, ConfigDict, Field


class EventType(StrEnum):
    CREDIT = "CREDIT"
    DEBIT = "DEBIT"


class EventCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    eventId: str
    accountId: str
    type: EventType
    amount: Annotated[float, Field(gt=0, description="Must be greater than 0")]
    currency: str
    eventTimestamp: datetime
    metadata: dict[str, Any] | None = None


class EventResponse(BaseModel):
    eventId: str
    accountId: str
    type: EventType
    amount: float
    currency: str
    eventTimestamp: datetime
    metadata: dict[str, Any] | None = None
    receivedAt: datetime


class BalanceResponse(BaseModel):
    accountId: str
    balance: float
    currency: str


class ErrorResponse(BaseModel):
    detail: str
