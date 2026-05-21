from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse
from sqlmodel import Session

from app.core.database import get_session
from app.core.exceptions import AccountNotFoundError
from app.models.schemas import BalanceResponse
from app.services.event_service import EventService

router = APIRouter(prefix="/accounts", tags=["Accounts"])


@router.get("/{account_id}/balance", response_model=BalanceResponse)
async def get_balance(account_id: str, session: Session = Depends(get_session)):
    service = EventService(session)
    try:
        return service.get_balance(account_id)
    except AccountNotFoundError as e:
        return JSONResponse(
            content={"detail": f"Account '{e.account_id}' not found"}, status_code=404
        )
