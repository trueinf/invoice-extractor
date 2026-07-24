from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class Settings:
    app_name: str = os.getenv("APP_NAME", "Invoice Extraction Service")
    data_dir: Path = Path(os.getenv("DATA_DIR", "./data")).resolve()
    database_path: Path = Path(os.getenv("DATABASE_PATH", "./data/app.db")).resolve()
    llm_base_url: str | None = os.getenv("LLM_BASE_URL")
    llm_api_key: str | None = os.getenv("LLM_API_KEY")
    llm_model: str = os.getenv("LLM_MODEL", "gpt-4.1-mini")
    llm_timeout_seconds: int = int(os.getenv("LLM_TIMEOUT_SECONDS", "90"))
    max_upload_bytes: int = int(os.getenv("MAX_UPLOAD_BYTES", str(20 * 1024 * 1024)))
    ocr_language: str = os.getenv("OCR_LANGUAGE", "eng")
    enable_ocr: bool = os.getenv("ENABLE_OCR", "true").lower() in {"1", "true", "yes", "on"}
    minimum_confidence_high: float = float(os.getenv("MIN_CONFIDENCE_HIGH", "0.85"))
    minimum_confidence_medium: float = float(os.getenv("MIN_CONFIDENCE_MEDIUM", "0.60"))
    cors_origins: tuple[str, ...] = tuple(
        origin.strip()
        for origin in os.getenv("CORS_ORIGINS", "*").split(",")
        if origin.strip()
    )

    def __post_init__(self) -> None:
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.database_path.parent.mkdir(parents=True, exist_ok=True)


settings = Settings()
