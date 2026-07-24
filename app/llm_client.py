from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any

import httpx

from .prompts import SYSTEM_PROMPT, build_user_prompt


@dataclass
class LLMResult:
    payload: dict[str, Any] | None
    raw_text: str | None = None
    error: str | None = None


class OpenAICompatibleClient:
    def __init__(self, base_url: str | None, api_key: str | None, model: str, timeout_seconds: int = 90):
        self.base_url = base_url.rstrip("/") if base_url else None
        self.api_key = api_key
        self.model = model
        self.timeout_seconds = timeout_seconds

    @property
    def enabled(self) -> bool:
        return bool(self.base_url and self.api_key)

    def _extract_json(self, text: str) -> dict[str, Any]:
        stripped = text.strip()
        if stripped.startswith("```"):
            stripped = stripped.strip("`")
            stripped = stripped.replace("json\n", "", 1).strip()
        return json.loads(stripped)

    def extract(self, raw_text: str, template: dict[str, Any]) -> LLMResult:
        if not self.enabled:
            return LLMResult(payload=None, error="LLM client is disabled")

        messages = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": build_user_prompt(raw_text, template)},
        ]

        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": 0,
        }

        headers = {"Authorization": f"Bearer {self.api_key}"}
        timeout = httpx.Timeout(self.timeout_seconds)

        try:
            with httpx.Client(base_url=self.base_url, headers=headers, timeout=timeout) as client:
                try:
                    response = client.post(
                        "/chat/completions",
                        json={**payload, "response_format": {"type": "json_object"}},
                    )
                    response.raise_for_status()
                except Exception:
                    response = client.post("/chat/completions", json=payload)
                    response.raise_for_status()

                data = response.json()
                content = data["choices"][0]["message"]["content"]
                parsed = self._extract_json(content)
                return LLMResult(payload=parsed, raw_text=content)
        except Exception as exc:  # pragma: no cover - network/runtime dependent
            return LLMResult(payload=None, error=str(exc))
