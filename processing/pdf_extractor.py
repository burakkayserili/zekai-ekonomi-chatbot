"""
Extract text from PDF files using pdfplumber.
"""

import logging
from pathlib import Path
from collections import Counter

import pdfplumber

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)


def clean_text(text: str) -> str:
    """Clean extracted text: fix whitespace, remove artifacts."""
    if not text:
        return ""
    # Normalize whitespace
    lines = text.split("\n")
    cleaned_lines = []
    for line in lines:
        line = line.strip()
        if line:
            cleaned_lines.append(line)
    text = "\n".join(cleaned_lines)
    # Remove excessive blank lines
    while "\n\n\n" in text:
        text = text.replace("\n\n\n", "\n\n")
    return text.strip()


def remove_repeated_headers(pages_text: list[str], threshold: float = 0.7) -> list[str]:
    """Remove text lines that appear on most pages (likely headers/footers)."""
    if len(pages_text) < 3:
        return pages_text

    # Count how often each line appears across pages
    line_counts = Counter()
    for page in pages_text:
        unique_lines = set(page.split("\n"))
        for line in unique_lines:
            stripped = line.strip()
            if stripped and len(stripped) > 3:
                line_counts[stripped] += 1

    # Lines appearing on >threshold of pages are likely headers/footers
    num_pages = len(pages_text)
    repeated_lines = {
        line for line, count in line_counts.items()
        if count / num_pages >= threshold
    }

    if not repeated_lines:
        return pages_text

    cleaned_pages = []
    for page in pages_text:
        lines = page.split("\n")
        filtered = [l for l in lines if l.strip() not in repeated_lines]
        cleaned_pages.append("\n".join(filtered))

    return cleaned_pages


def extract_text_from_pdf(pdf_path: str | Path) -> dict:
    """
    Extract text from a PDF file.

    Returns:
        dict with keys: text, pages, metadata, success
    """
    pdf_path = Path(pdf_path)
    result = {
        "text": "",
        "pages": [],
        "metadata": {
            "file_path": str(pdf_path),
            "file_name": pdf_path.name,
            "num_pages": 0,
        },
        "success": False,
    }

    if not pdf_path.exists():
        logger.warning(f"PDF not found: {pdf_path}")
        return result

    try:
        with pdfplumber.open(pdf_path) as pdf:
            result["metadata"]["num_pages"] = len(pdf.pages)
            pages_text = []

            for i, page in enumerate(pdf.pages):
                try:
                    text = page.extract_text() or ""
                    text = clean_text(text)
                    pages_text.append(text)
                    result["pages"].append({
                        "page_num": i + 1,
                        "text": text,
                    })
                except Exception as e:
                    logger.warning(f"Error extracting page {i+1} from {pdf_path.name}: {e}")
                    pages_text.append("")
                    result["pages"].append({"page_num": i + 1, "text": ""})

            # Remove repeated headers/footers
            cleaned_pages = remove_repeated_headers(pages_text)
            for i, cleaned in enumerate(cleaned_pages):
                result["pages"][i]["text"] = cleaned

            # Combine all pages
            result["text"] = "\n\n".join(cleaned_pages)
            result["success"] = bool(result["text"].strip())

            if not result["success"]:
                logger.warning(f"No text extracted from {pdf_path.name} (may be scanned/image-based)")

    except Exception as e:
        logger.error(f"Failed to process {pdf_path.name}: {e}")

    return result
