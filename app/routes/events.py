from fastapi import APIRouter, Depends, Query, Request
from fastapi.responses import JSONResponse
from sqlmodel import Session

from app.core.database import get_session
from app.core.exceptions import EventNotFoundError
from app.models.schemas import EventCreate, EventResponse
from app.services.event_service import EventService

router = APIRouter(prefix="/events", tags=["Events"])


@router.post("")
async def submit_event(
    payload: EventCreate, request: Request, session: Session = Depends(get_session)
):
    service = EventService(session)
    try:
        event_response, created = service.submit(
            payload, request.client.host if request.client else None
        )
        return JSONResponse(
            content=event_response.model_dump(mode="json"),
            status_code=201 if created else 200,
        )
    except EventNotFoundError as e:
        return JSONResponse(content={"detail": str(e)}, status_code=404)
    except Exception:
        return JSONResponse(
            content={"detail": "Internal server error"}, status_code=500
        )


@router.get("/{event_id}", response_model=EventResponse)
async def get_event(event_id: str, session: Session = Depends(get_session)):
    service = EventService(session)
    try:
        return service.get_by_id(event_id)
    except EventNotFoundError as e:
        return JSONResponse(
            content={"detail": f"Event '{e.event_id}' not found"}, status_code=404
        )


@router.get("")
async def list_events(
    account: str = Query(..., description="Account ID"),
    session: Session = Depends(get_session),
):
    service = EventService(session)
    return service.list_by_account(account)
