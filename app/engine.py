from __future__ import annotations

from copy import deepcopy
from typing import Any

from .config import settings
from .document_loader import load_document_text
from .heuristics import extract_heuristics
from .llm_client import OpenAICompatibleClient
from .template import clone_template
from .validator import confidence_report, normalize_output, validate_output


def _is_blank_value(value: Any) -> bool:
    if value in (None, "", [], {}):
        return True
    if isinstance(value, dict):
        return all(_is_blank_value(item) for item in value.values())
    if isinstance(value, list):
        return all(_is_blank_value(item) for item in value)
    return False



def deep_merge(base: Any, update: Any) -> Any:
    if update is None:
        return deepcopy(base)
    if isinstance(base, dict) and isinstance(update, dict):
        merged = deepcopy(base)
        for key, value in update.items():
            if key not in merged:
                merged[key] = deepcopy(value)
                continue
            if value is None:
                continue
            merged[key] = deep_merge(merged[key], value)
        return merged
    if isinstance(base, list) and isinstance(update, list):
        if update and not all(_is_blank_value(item) for item in update):
            return deepcopy(update)
        return deepcopy(base)
    if update in (None, ""):
        return deepcopy(base)
    return deepcopy(update)


class InvoiceExtractionEngine:
    def __init__(self, settings_obj=settings):
        self.settings = settings_obj
        self.llm = OpenAICompatibleClient(
            base_url=settings_obj.llm_base_url,
            api_key=settings_obj.llm_api_key,
            model=settings_obj.llm_model,
            timeout_seconds=settings_obj.llm_timeout_seconds,
        )

    def extract(self, file_bytes: bytes, filename: str) -> dict[str, Any]:
        document = load_document_text(
            file_bytes=file_bytes,
            filename=filename,
            enable_ocr=self.settings.enable_ocr,
            ocr_language=self.settings.ocr_language,
        )

        result = clone_template()
        heuristic = extract_heuristics(document.text)
        result = deep_merge(result, heuristic)

        llm_result = self.llm.extract(document.text, result)
        if llm_result.payload:
            result = deep_merge(result, llm_result.payload)
            if llm_result.error and llm_result.error != "LLM client is disabled":
                result.setdefault("additional", {})
                result["additional"]["notes"] = f"LLM fallback error: {llm_result.error}"
        elif llm_result.error and llm_result.error != "LLM client is disabled":
            result.setdefault("additional", {})
            result["additional"]["notes"] = llm_result.error

        result["document_meta"]["page_count"] = document.page_count
        if not result["document_meta"].get("language"):
            result["document_meta"]["language"] = _guess_language(document.text)
        if document.warnings:
            existing = result.get("additional", {}).get("notes")
            note = " | ".join(document.warnings)
            if existing:
                result["additional"]["notes"] = f"{existing} | {note}"
            else:
                result["additional"]["notes"] = note

        result = normalize_output(result)
        result["validation"] = validate_output(result)
        result["extraction_confidence"] = confidence_report(result)
        return result



def _guess_language(text: str) -> str | None:
    if not text:
        return None
    ascii_ratio = sum(1 for char in text if ord(char) < 128) / max(len(text), 1)
    return "en" if ascii_ratio > 0.85 else None
