from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class JobStatus(str, Enum):
    queued = "queued"
    processing = "processing"
    completed = "completed"
    failed = "failed"


class ExtractionJobCreateResponse(BaseModel):
    job_id: str
    status: JobStatus
    filename: str
    content_type: str | None = None
    created_at: datetime
    updated_at: datetime
    file_size: int
    sha256: str
    status_url: str
    result_url: str


class ExtractionJobResponse(BaseModel):
    job_id: str
    status: JobStatus
    filename: str
    content_type: str | None = None
    file_size: int
    sha256: str
    created_at: datetime
    updated_at: datetime
    result: dict[str, Any] | None = None
    error_message: str | None = None
    extracted_via: str | None = None
    page_count: int | None = None

    model_config = ConfigDict(from_attributes=True)


class ExtractionResultResponse(BaseModel):
    job_id: str
    status: JobStatus
    result: dict[str, Any]


class SyncExtractionResponse(BaseModel):
    job_id: str
    status: JobStatus
    filename: str
    file_size: int
    sha256: str
    result: dict[str, Any]


class ErrorResponse(BaseModel):
    detail: str
    job_id: str | None = None
    status: str | None = None


class ExtractionOptions(BaseModel):
    mode: str = Field(default="async", pattern="^(async|sync)$")
