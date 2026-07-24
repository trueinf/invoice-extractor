from __future__ import annotations

from dataclasses import dataclass, field
from io import BytesIO
from pathlib import Path
from typing import Any

import pdfplumber
from PIL import Image, ImageSequence

try:
    import fitz  # PyMuPDF
except Exception:  # pragma: no cover - optional runtime dependency
    fitz = None

try:
    import pytesseract
except Exception:  # pragma: no cover - optional runtime dependency
    pytesseract = None


@dataclass
class DocumentText:
    filename: str
    page_count: int
    text: str
    page_texts: list[str]
    warnings: list[str] = field(default_factory=list)
    extracted_via: str = "pdf_text"


def _append_table_text(page: Any) -> str:
    parts: list[str] = []
    try:
        tables = page.extract_tables() or []
    except Exception:
        tables = []
    for table in tables:
        for row in table or []:
            row_text = " | ".join((cell or "").strip() for cell in row)
            row_text = row_text.strip(" |")
            if row_text:
                parts.append(row_text)
    return "\n".join(parts)


def _ocr_image(image: Image.Image, language: str) -> str:
    if pytesseract is None:
        return ""
    try:
        return pytesseract.image_to_string(image, lang=language)
    except Exception:
        return ""


def _extract_from_image_bytes(file_bytes: bytes, language: str) -> tuple[list[str], list[str], str]:
    if pytesseract is None:
        return [""], ["OCR unavailable; pytesseract could not be imported."], "image"

    warnings: list[str] = []
    page_texts: list[str] = []
    try:
        image = Image.open(BytesIO(file_bytes))
    except Exception as exc:
        return [""], [f"Unable to open image: {exc}"], "image"

    try:
        frames = list(ImageSequence.Iterator(image)) if getattr(image, "is_animated", False) else [image]
    except Exception:
        frames = [image]

    for frame in frames:
        text = _ocr_image(frame, language)
        page_texts.append(text.strip())
        if not text.strip():
            warnings.append("OCR produced no text for one image page.")

    return page_texts, warnings, "ocr"


def _ocr_pdf_pages(file_bytes: bytes, language: str) -> tuple[list[str], list[str], str]:
    if fitz is None or pytesseract is None:
        return [""], ["OCR for PDFs is unavailable because PyMuPDF or pytesseract is missing."], "pdf_text"

    warnings: list[str] = []
    page_texts: list[str] = []
    try:
        doc = fitz.open(stream=file_bytes, filetype="pdf")
    except Exception as exc:
        return [""], [f"Unable to open PDF for OCR: {exc}"], "pdf_text"

    for page in doc:
        try:
            pix = page.get_pixmap(matrix=fitz.Matrix(2, 2), alpha=False)
            image = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
            text = _ocr_image(image, language)
            page_texts.append(text.strip())
            if not text.strip():
                warnings.append("OCR produced no text for one PDF page.")
        except Exception as exc:
            page_texts.append("")
            warnings.append(f"OCR failed for one PDF page: {exc}")

    return page_texts, warnings, "ocr"



def load_document_text(file_bytes: bytes, filename: str, enable_ocr: bool = True, ocr_language: str = "eng") -> DocumentText:
    suffix = Path(filename.lower()).suffix
    warnings: list[str] = []

    if suffix == ".pdf":
        page_texts: list[str] = []
        extracted_via = "pdf_text"
        with pdfplumber.open(BytesIO(file_bytes)) as pdf:
            page_count = len(pdf.pages)
            for page in pdf.pages:
                text = (page.extract_text() or "").strip()
                table_text = _append_table_text(page)
                combined = "\n".join(part for part in [text, table_text] if part).strip()
                page_texts.append(combined)

        if enable_ocr and any(not page.strip() for page in page_texts):
            if fitz is not None and pytesseract is not None:
                try:
                    doc = fitz.open(stream=file_bytes, filetype="pdf")
                    for index, current_text in enumerate(page_texts):
                        if current_text.strip():
                            continue
                        page = doc[index]
                        pix = page.get_pixmap(matrix=fitz.Matrix(2, 2), alpha=False)
                        image = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
                        ocr_text = _ocr_image(image, ocr_language).strip()
                        if ocr_text:
                            page_texts[index] = ocr_text
                            extracted_via = "ocr"
                        else:
                            warnings.append(f"OCR produced no text for PDF page {index + 1}.")
                except Exception as exc:
                    warnings.append(f"PDF OCR fallback failed: {exc}")
            else:
                warnings.append("OCR for PDFs is unavailable because PyMuPDF or pytesseract is missing.")

        return DocumentText(
            filename=filename,
            page_count=page_count,
            text="\n\n--- PAGE BREAK ---\n\n".join(page_texts).strip(),
            page_texts=page_texts,
            warnings=warnings,
            extracted_via=extracted_via,
        )

    page_texts, warnings, extracted_via = _extract_from_image_bytes(file_bytes, ocr_language if enable_ocr else "eng")
    return DocumentText(
        filename=filename,
        page_count=len(page_texts),
        text="\n\n--- PAGE BREAK ---\n\n".join(page_texts).strip(),
        page_texts=page_texts,
        warnings=warnings,
        extracted_via=extracted_via,
    )
