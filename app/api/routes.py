"""HTTP routes. Thin layer: validate -> call service -> shape response."""
from fastapi import APIRouter, Depends, Request

from app.core.config import Settings, get_settings
from app.models.schemas import (
    HealthResponse,
    IngestRequest,
    IngestResponse,
    ProcessedResult,
)
from app.services.ingestion import IngestionService

router = APIRouter()

# Single shared service instance for the app's lifetime. For a real
# datastore you'd wire this through app.state or a DI provider instead.
_service: IngestionService | None = None


def get_service(settings: Settings = Depends(get_settings)) -> IngestionService:
    global _service
    if _service is None:
        _service = IngestionService(max_batch_size=settings.max_batch_size)
    return _service


@router.get("/health", response_model=HealthResponse, tags=["ops"])
def health(settings: Settings = Depends(get_settings)) -> HealthResponse:
    """Liveness/readiness probe. DigitalOcean App Platform can hit this."""
    return HealthResponse(status="ok", environment=settings.environment)


@router.post("/api/v1/ingest", response_model=IngestResponse, tags=["ingestion"])
def ingest(
    payload: IngestRequest,
    request: Request,
    service: IngestionService = Depends(get_service),
) -> IngestResponse:
    request_id = getattr(request.state, "request_id", "unknown")
    accepted, rejected = service.ingest(payload.records)
    return IngestResponse(accepted=accepted, rejected=rejected, request_id=request_id)


@router.get("/api/v1/results", response_model=ProcessedResult, tags=["processing"])
def results(service: IngestionService = Depends(get_service)) -> ProcessedResult:
    return service.process()
