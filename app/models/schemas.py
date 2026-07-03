"""Request/response models.

Pydantic gives us validation for free: bad input is rejected with a 422
before it ever reaches business logic. Swap these fields for whatever the
real challenge's data shape turns out to be.
"""
from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field, field_validator


class DataRecord(BaseModel):
    """A single unit of ingested data. Placeholder shape — adapt on the day."""

    id: str = Field(..., min_length=1, max_length=128)
    source: str = Field(..., min_length=1, max_length=128)
    timestamp: datetime
    value: float
    metadata: dict[str, Any] = Field(default_factory=dict)

    @field_validator("value")
    @classmethod
    def value_must_be_finite(cls, v: float) -> float:
        if v != v or v in (float("inf"), float("-inf")):  # NaN / inf guard
            raise ValueError("value must be a finite number")
        return v


class IngestRequest(BaseModel):
    records: list[DataRecord] = Field(..., min_length=1)


class IngestResponse(BaseModel):
    accepted: int
    rejected: int
    request_id: str


class ProcessedResult(BaseModel):
    count: int
    sum: float
    mean: float
    min: float
    max: float


class HealthResponse(BaseModel):
    status: str
    environment: str


class ErrorResponse(BaseModel):
    error: str
    detail: str | None = None
    request_id: str | None = None
