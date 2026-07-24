from __future__ import annotations

from functools import lru_cache

from .config import settings
from .engine import InvoiceExtractionEngine
from .job_store import JobStore
from .service import ExtractionService
from .storage import LocalFileStorage


@lru_cache(maxsize=1)
def get_job_store() -> JobStore:
    return JobStore(settings.database_path)


@lru_cache(maxsize=1)
def get_storage() -> LocalFileStorage:
    return LocalFileStorage(settings.data_dir)


@lru_cache(maxsize=1)
def get_engine() -> InvoiceExtractionEngine:
    return InvoiceExtractionEngine(settings)


@lru_cache(maxsize=1)
def get_service() -> ExtractionService:
    return ExtractionService(get_job_store(), get_storage(), get_engine())
