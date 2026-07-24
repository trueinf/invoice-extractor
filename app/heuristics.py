from __future__ import annotations

import re
from decimal import Decimal, InvalidOperation
from typing import Any

from dateutil import parser as date_parser

from .template import clone_template

CURRENCY_SYMBOLS = {"$", "€", "£", "₹"}

INVOICE_NUMBER_PATTERNS = [
    re.compile(r"(?:invoice\s*(?:no\.?|number|#)\s*[:\-]?)\s*(?P<value>[A-Z0-9\-\/]+)", re.I),
    re.compile(r"\binv(?:oice)?\s*#?\s*(?P<value>[A-Z0-9\-\/]+)", re.I),
]
DATE_PATTERNS = {
    "invoice_date": [re.compile(r"(?:invoice\s*date|date)\s*[:\-]?\s*(?P<value>[^\n\r]+)", re.I)],
    "due_date": [re.compile(r"(?:due\s*date)\s*[:\-]?\s*(?P<value>[^\n\r]+)", re.I)],
    "issue_date": [re.compile(r"(?:issue\s*date)\s*[:\-]?\s*(?P<value>[^\n\r]+)", re.I)],
    "period_start": [re.compile(r"(?:period\s*start|from)\s*[:\-]?\s*(?P<value>[^\n\r]+)", re.I)],
    "period_end": [re.compile(r"(?:period\s*end|to)\s*[:\-]?\s*(?P<value>[^\n\r]+)", re.I)],
}
AMOUNT_PATTERNS = {
    "subtotal": [re.compile(r"(?:subtotal|sub\s*total|amount\s*before\s*tax)\s*[:\-]?\s*(?P<value>[-$€£₹0-9,\.() ]+)", re.I)],
    "total_tax": [re.compile(r"(?:total\s*tax|tax\s*total)\s*[:\-]?\s*(?P<value>[-$€£₹0-9,\.() ]+)", re.I)],
    "grand_total": [re.compile(r"(?:grand\s*total|total\s*due|amount\s*due|balance\s*due|invoice\s*total)\s*[:\-]?\s*(?P<value>[-$€£₹0-9,\.() ]+)", re.I)],
    "cgst": [re.compile(r"(?:cgst)\s*[:\-]?\s*(?P<value>[-$€£₹0-9,\.() ]+)", re.I)],
    "sgst": [re.compile(r"(?:sgst)\s*[:\-]?\s*(?P<value>[-$€£₹0-9,\.() ]+)", re.I)],
    "igst": [re.compile(r"(?:igst)\s*[:\-]?\s*(?P<value>[-$€£₹0-9,\.() ]+)", re.I)],
    "round_off": [re.compile(r"(?:round\s*off|rounding)\s*[:\-]?\s*(?P<value>[-$€£₹0-9,\.() ]+)", re.I)],
}

LINE_TOTAL_RE = re.compile(r"(?P<amount>[-$€£₹]?[\d,]+(?:\.\d+)?)\s*$")
KEYWORD_SKIP = {
    "subtotal",
    "sub total",
    "grand total",
    "amount due",
    "balance due",
    "total tax",
    "invoice total",
    "vat",
    "igst",
    "cgst",
    "sgst",
    "tax",
}


def _first_match(patterns: list[re.Pattern[str]], text: str) -> str | None:
    for pattern in patterns:
        match = pattern.search(text)
        if match:
            value = match.group("value").strip()
            return value
    return None



def _parse_money(value: str | None) -> float | None:
    if value is None:
        return None
    cleaned = value.strip().replace(",", "").replace(" ", "")
    cleaned = cleaned.replace("$", "").replace("€", "").replace("£", "").replace("₹", "")
    cleaned = cleaned.replace("(", "-").replace(")", "")
    if not cleaned:
        return None
    try:
        return float(Decimal(cleaned))
    except (InvalidOperation, ValueError):
        return None



def _parse_date(value: str | None) -> str | None:
    if not value:
        return None
    try:
        return date_parser.parse(value, fuzzy=True, dayfirst=False).date().isoformat()
    except Exception:
        return value.strip()



def _detect_currency_symbol(text: str) -> str | None:
    for symbol in CURRENCY_SYMBOLS:
        if symbol in text:
            return symbol
    return None



def _extract_supplier_name(lines: list[str]) -> str | None:
    for line in lines[:12]:
        lowered = line.lower()
        if not line or any(keyword in lowered for keyword in ["invoice", "bill to", "ship to", "tax invoice", "credit note", "date", "due date"]):
            continue
        if len(line) < 3:
            continue
        if re.fullmatch(r"[\d\W]+", line):
            continue
        return line.strip()
    return None



def _extract_customer_name(lines: list[str]) -> str | None:
    patterns = [r"bill to[:\s]*", r"billed to[:\s]*", r"invoice to[:\s]*", r"sold to[:\s]*", r"customer[:\s]*"]
    for index, line in enumerate(lines):
        lowered = line.lower()
        for pattern in patterns:
            if re.match(pattern, lowered):
                remainder = re.sub(pattern, "", line, flags=re.I).strip()
                if remainder:
                    return remainder
                for follow in lines[index + 1 : index + 4]:
                    follow = follow.strip()
                    if follow and not re.fullmatch(r"[\d\W]+", follow):
                        return follow
    return None



def _extract_line_items(lines: list[str]) -> list[dict[str, Any]]:
    items: list[dict[str, Any]] = []
    start_index = 0
    end_index = len(lines)

    for index, line in enumerate(lines):
        if re.search(r"description|qty|quantity|rate|unit price|amount", line, re.I):
            start_index = max(0, index)
            break

    for index in range(start_index, len(lines)):
        line = lines[index].strip()
        lowered = line.lower()
        if any(keyword in lowered for keyword in KEYWORD_SKIP):
            end_index = index
            break

    candidate_lines = lines[start_index:end_index]
    for line in candidate_lines:
        raw = line.strip()
        if not raw:
            continue
        if any(keyword in raw.lower() for keyword in KEYWORD_SKIP):
            continue
        if "|" in raw:
            cells = [cell.strip() for cell in raw.split("|") if cell.strip()]
            if len(cells) >= 2:
                maybe_amount = _parse_money(cells[-1])
                if maybe_amount is not None:
                    item = {
                        "description": cells[0],
                        "line_total": maybe_amount,
                    }
                    if len(cells) >= 3:
                        qty = _parse_money(cells[1])
                        if qty is not None:
                            item["quantity"] = qty
                    items.append(item)
                    continue

        match = LINE_TOTAL_RE.search(raw)
        if match:
            amount = _parse_money(match.group("amount"))
            if amount is None:
                continue
            description = raw[: match.start("amount")].strip(" -\t")
            if len(description) >= 2:
                items.append({"description": description, "line_total": amount})

    seen: set[tuple[str, float]] = set()
    deduped: list[dict[str, Any]] = []
    for item in items:
        key = (str(item.get("description", "")).lower(), float(item.get("line_total", 0.0) or 0.0))
        if key in seen:
            continue
        seen.add(key)
        deduped.append(item)
    return deduped



def extract_heuristics(text: str) -> dict[str, Any]:
    output = clone_template()
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    joined = "\n".join(lines)

    invoice_number = _first_match(INVOICE_NUMBER_PATTERNS, joined)
    if invoice_number:
        output["document_meta"]["invoice_number"] = invoice_number

    for field, patterns in DATE_PATTERNS.items():
        value = _first_match(patterns, joined)
        if value:
            output["document_meta"][field] = _parse_date(value)
            if field == "invoice_date":
                output["document_meta"]["invoice_date_raw"] = value

    if not output["document_meta"].get("document_type"):
        lowered = joined.lower()
        if "credit note" in lowered or "credit memo" in lowered:
            output["document_meta"]["document_type"] = "credit_note"
            output["document_meta"]["is_credit_note"] = True
        else:
            output["document_meta"]["document_type"] = "invoice"
            output["document_meta"]["is_credit_note"] = False

    currency_symbol = _detect_currency_symbol(joined)
    if currency_symbol:
        output["totals"]["currency_symbol"] = currency_symbol
        output["totals"]["currency_code"] = {"$": "USD", "€": "EUR", "£": "GBP", "₹": "INR"}.get(currency_symbol)

    for field, patterns in AMOUNT_PATTERNS.items():
        value = _first_match(patterns, joined)
        if value:
            output["totals"][field] = _parse_money(value)

    output["supplier"]["name"] = _extract_supplier_name(lines)
    output["customer"]["name"] = _extract_customer_name(lines)
    output["line_items"] = _extract_line_items(lines)

    if lines:
        output["additional"]["footer_text"] = lines[-1]
    return output
