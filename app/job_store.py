from __future__ import annotations

import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .models import JobStatus


class JobStore:
    def __init__(self, db_path: str | Path):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS extraction_jobs (
                    job_id TEXT PRIMARY KEY,
                    status TEXT NOT NULL,
                    filename TEXT NOT NULL,
                    content_type TEXT,
                    file_path TEXT NOT NULL,
                    file_size INTEGER NOT NULL,
                    sha256 TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    result_json TEXT,
                    error_message TEXT,
                    extracted_via TEXT,
                    page_count INTEGER
                )
                """
            )
            conn.execute("CREATE INDEX IF NOT EXISTS idx_extraction_jobs_status ON extraction_jobs(status)")
            conn.commit()

    def _now(self) -> str:
        return datetime.now(timezone.utc).isoformat()

    def create_job(
        self,
        *,
        job_id: str,
        filename: str,
        content_type: str | None,
        file_path: str,
        file_size: int,
        sha256: str,
        status: JobStatus = JobStatus.queued,
    ) -> dict[str, Any]:
        now = self._now()
        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO extraction_jobs (
                    job_id, status, filename, content_type, file_path, file_size, sha256,
                    created_at, updated_at, result_json, error_message, extracted_via, page_count
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, NULL, NULL, NULL, NULL)
                """,
                (job_id, status.value, filename, content_type, file_path, file_size, sha256, now, now),
            )
            conn.commit()
        return self.get_job(job_id)

    def update_job(self, job_id: str, **fields: Any) -> dict[str, Any]:
        if not fields:
            return self.get_job(job_id)

        allowed = {
            "status",
            "result_json",
            "error_message",
            "extracted_via",
            "page_count",
            "file_path",
            "filename",
            "content_type",
            "file_size",
            "sha256",
        }
        updates = {key: value for key, value in fields.items() if key in allowed}
        if "status" in updates and isinstance(updates["status"], JobStatus):
            updates["status"] = updates["status"].value
        updates["updated_at"] = self._now()

        columns = ", ".join(f"{key} = ?" for key in updates)
        values = list(updates.values()) + [job_id]
        with self._connect() as conn:
            conn.execute(f"UPDATE extraction_jobs SET {columns} WHERE job_id = ?", values)
            conn.commit()
        return self.get_job(job_id)

    def complete_job(self, job_id: str, result: dict[str, Any], *, extracted_via: str | None = None, page_count: int | None = None) -> dict[str, Any]:
        payload = json.dumps(result, ensure_ascii=False)
        return self.update_job(
            job_id,
            status=JobStatus.completed,
            result_json=payload,
            error_message=None,
            extracted_via=extracted_via,
            page_count=page_count,
        )

    def fail_job(self, job_id: str, error_message: str) -> dict[str, Any]:
        return self.update_job(
            job_id,
            status=JobStatus.failed,
            error_message=error_message,
            result_json=None,
        )

    def get_job(self, job_id: str) -> dict[str, Any] | None:
        with self._connect() as conn:
            row = conn.execute("SELECT * FROM extraction_jobs WHERE job_id = ?", (job_id,)).fetchone()
        if row is None:
            return None
        record = dict(row)
        record["status"] = JobStatus(record["status"])
        if record.get("result_json"):
            record["result"] = json.loads(record["result_json"])
        else:
            record["result"] = None
        return record

    def list_recent_jobs(self, limit: int = 20) -> list[dict[str, Any]]:
        with self._connect() as conn:
            rows = conn.execute(
                "SELECT * FROM extraction_jobs ORDER BY created_at DESC LIMIT ?",
                (limit,),
            ).fetchall()
        jobs = []
        for row in rows:
            record = dict(row)
            record["status"] = JobStatus(record["status"])
            if record.get("result_json"):
                record["result"] = json.loads(record["result_json"])
            else:
                record["result"] = None
            jobs.append(record)
        return jobs
