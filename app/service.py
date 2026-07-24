from __future__ import annotations

from typing import Any
from uuid import uuid4

from fastapi import BackgroundTasks

from .engine import InvoiceExtractionEngine
from .job_store import JobStore
from .models import JobStatus
from .storage import LocalFileStorage


class ExtractionService:
    def __init__(self, store: JobStore, storage: LocalFileStorage, engine: InvoiceExtractionEngine):
        self.store = store
        self.storage = storage
        self.engine = engine

    def submit(self, *, file_bytes: bytes, filename: str, content_type: str | None, background_tasks: BackgroundTasks | None = None) -> dict[str, Any]:
        job_id = uuid4().hex
        saved = self.storage.save(file_bytes, job_id=job_id, filename=filename)
        job = self.store.create_job(
            job_id=job_id,
            filename=filename,
            content_type=content_type,
            file_path=str(saved.path),
            file_size=saved.size,
            sha256=saved.sha256,
            status=JobStatus.queued,
        )
        if background_tasks is not None:
            background_tasks.add_task(self.process_job, job_id)
        return job

    def process_job(self, job_id: str) -> dict[str, Any]:
        job = self.store.get_job(job_id)
        if job is None:
            raise ValueError(f"Unknown job_id: {job_id}")

        self.store.update_job(job_id, status=JobStatus.processing)
        try:
            file_bytes = self.storage.read(job["file_path"])
            result = self.engine.extract(file_bytes, job["filename"])
            updated = self.store.complete_job(
                job_id,
                result,
                extracted_via=result.get("additional", {}).get("extraction_via"),
                page_count=result.get("document_meta", {}).get("page_count"),
            )
            return updated
        except Exception as exc:
            self.store.fail_job(job_id, str(exc))
            return self.store.get_job(job_id) or {"job_id": job_id, "status": JobStatus.failed}

    def process_sync(self, *, file_bytes: bytes, filename: str, content_type: str | None) -> dict[str, Any]:
        job_id = uuid4().hex
        saved = self.storage.save(file_bytes, job_id=job_id, filename=filename)
        self.store.create_job(
            job_id=job_id,
            filename=filename,
            content_type=content_type,
            file_path=str(saved.path),
            file_size=saved.size,
            sha256=saved.sha256,
            status=JobStatus.processing,
        )
        try:
            result = self.engine.extract(file_bytes, filename)
            self.store.complete_job(
                job_id,
                result,
                extracted_via=result.get("additional", {}).get("extraction_via"),
                page_count=result.get("document_meta", {}).get("page_count"),
            )
            job = self.store.get_job(job_id)
            assert job is not None
            job["result"] = result
            return job
        except Exception as exc:
            self.store.fail_job(job_id, str(exc))
            return self.store.get_job(job_id) or {"job_id": job_id, "status": JobStatus.failed}
