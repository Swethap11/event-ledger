from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse
from sqlmodel import Session

from app.core.database import get_session
from app.core.exceptions import AccountNotFoundError
from app.services.event_service import EventService

router = APIRouter(prefix="/accounts", tags=["Accounts"])


@router.get("/{account_id}/balance")
async def get_balance(account_id: str, session: Session = Depends(get_session)):
    service = EventService(session)
    try:
        return service.get_balance(account_id)
    except AccountNotFoundError:
        return JSONResponse(
            status_code=404,
            content={"detail": f"Account '{account_id}' not found"},
        )
