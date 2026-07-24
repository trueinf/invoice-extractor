from __future__ import annotations

import json
from textwrap import dedent
from typing import Any

from .template import DEFAULT_OUTPUT


SYSTEM_PROMPT = dedent(
    """
    You are an invoice data extraction engine.
    Extract all information from the attached invoice and return it as structured JSON only.
    No preamble, no explanation, and no markdown fences.

    Rules:
    - If a field is not present on the invoice, set it to null.
    - Do not guess or infer.
    - Preserve values exactly as printed.
    - Currency symbols must be stripped into separate currency fields where possible.
    - Dates must be normalized to ISO YYYY-MM-DD, while raw strings should be retained when a raw field exists.
    - All monetary values must be numbers, with no thousand separators.
    - Extract every line item; do not truncate.
    - If text is illegible, set the value to "UNREADABLE".
    - Set confidence per section as high / medium / low.
    - Return valid JSON that matches the requested schema.
    """
).strip()



def build_user_prompt(raw_text: str, template: dict[str, Any] | None = None) -> str:
    schema = template or DEFAULT_OUTPUT
    return dedent(
        f"""
        Fill the following invoice extraction schema from the document text below.

        Output schema:
        {json.dumps(schema, indent=2, ensure_ascii=False)}

        Document text:
        ---
        {raw_text}
        ---

        Output only JSON.
        """
    ).strip()
