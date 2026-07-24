from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass
from pathlib import Path


_SAFE_FILENAME_RE = re.compile(r"[^A-Za-z0-9._-]+")


@dataclass(frozen=True)
class SavedFile:
    path: Path
    sha256: str
    size: int


class LocalFileStorage:
    def __init__(self, base_dir: str | Path):
        self.base_dir = Path(base_dir)
        self.upload_dir = self.base_dir / "uploads"
        self.upload_dir.mkdir(parents=True, exist_ok=True)

    def _safe_name(self, filename: str) -> str:
        stem = Path(filename).stem or "invoice"
        suffix = Path(filename).suffix.lower() or ".bin"
        safe = _SAFE_FILENAME_RE.sub("_", stem).strip("._") or "invoice"
        return f"{safe}{suffix}"

    def save(self, file_bytes: bytes, job_id: str, filename: str) -> SavedFile:
        safe_name = self._safe_name(filename)
        path = self.upload_dir / f"{job_id}_{safe_name}"
        path.write_bytes(file_bytes)
        digest = hashlib.sha256(file_bytes).hexdigest()
        return SavedFile(path=path, sha256=digest, size=len(file_bytes))

    def read(self, path: str | Path) -> bytes:
        return Path(path).read_bytes()

    def delete(self, path: str | Path) -> None:
        try:
            Path(path).unlink()
        except FileNotFoundError:
            pass
