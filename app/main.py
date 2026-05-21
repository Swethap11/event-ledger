from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.core.database import init_db
from app.core.logging_config import get_logger
from app.routes import accounts, events

app = FastAPI(
    title="Event Ledger API",
    description="Idempotent financial ledger with out-of-order event support.",
    version="1.0.0",
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_methods=["GET", "POST"],
)

# Include routers
app.include_router(events.router)
app.include_router(accounts.router)


@app.on_event("startup")
async def startup_event():
    init_db()


@app.get("/health")
async def health_check():
    return {"status": "ok"}


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger = get_logger()
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"},
    )
