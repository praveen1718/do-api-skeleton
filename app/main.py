"""Application entrypoint: builds the FastAPI app, wires middleware,
error handling, and structured logging.
"""
import logging
import uuid

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from app.api.routes import router
from app.core.config import get_settings
from app.core.logging import configure_logging

settings = get_settings()
configure_logging(settings.log_level)
log = logging.getLogger("app")

app = FastAPI(
    title=settings.app_name,
    version="0.1.0",
    description="Data ingestion & processing REST API (interview skeleton).",
)


@app.middleware("http")
async def add_request_context(request: Request, call_next):
    """Assign a request_id, log start/end, and time each request."""
    request_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))
    request.state.request_id = request_id
    log.info("request.start", extra={"request_id": request_id})
    try:
        response = await call_next(request)
    except Exception:
        log.exception("request.error", extra={"request_id": request_id})
        raise
    response.headers["X-Request-ID"] = request_id
    log.info("request.done", extra={"request_id": request_id})
    return response


@app.exception_handler(RequestValidationError)
async def validation_handler(request: Request, exc: RequestValidationError):
    """Return a clean 422 instead of FastAPI's default verbose body."""
    return JSONResponse(
        status_code=422,
        content={
            "error": "validation_error",
            "detail": exc.errors(),
            "request_id": getattr(request.state, "request_id", None),
        },
    )


@app.exception_handler(Exception)
async def unhandled_handler(request: Request, exc: Exception):
    """Never leak stack traces to clients; log them, return a generic 500."""
    return JSONResponse(
        status_code=500,
        content={
            "error": "internal_error",
            "request_id": getattr(request.state, "request_id", None),
        },
    )


app.include_router(router)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("app.main:app", host=settings.host, port=settings.port, reload=True)
