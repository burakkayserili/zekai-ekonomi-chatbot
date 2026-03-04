"""
Download PDFs from TCMB website to local disk.
"""

import json
import time
import logging
import re
from pathlib import Path
from urllib.parse import unquote, urlparse

import requests
from tqdm import tqdm

from config import PDF_DIR, METADATA_FILE, REQUEST_DELAY, REQUEST_TIMEOUT, USER_AGENT
from scraper.url_registry import PUBLICATION_SOURCES

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

SESSION = requests.Session()
SESSION.headers.update({"User-Agent": USER_AGENT})


def sanitize_filename(name: str) -> str:
    """Create a safe filename from a string."""
    # Remove or replace unsafe characters
    name = re.sub(r'[<>:"/\\|?*]', '_', name)
    name = re.sub(r'\s+', '_', name)
    name = name.strip('._')
    # Limit length
    if len(name) > 150:
        name = name[:150]
    return name


def get_filename_from_pdf(pdf_info: dict) -> str:
    """Generate a meaningful filename for a PDF."""
    url = pdf_info["url"]
    title = pdf_info.get("title", "")
    category = pdf_info.get("category", "unknown")
    year = pdf_info.get("year", "")

    # Try to extract filename from URL
    parsed = urlparse(url)
    url_filename = unquote(parsed.path.split("/")[-1])

    if url_filename.lower().endswith(".pdf"):
        return sanitize_filename(url_filename)

    # Build filename from metadata
    if title:
        base = sanitize_filename(title)
    else:
        base = sanitize_filename(f"{category}_{year}")

    if not base.lower().endswith(".pdf"):
        base += ".pdf"

    return base


def download_pdf(url: str, save_path: Path, max_retries: int = 3) -> bool:
    """Download a single PDF file with retry logic."""
    for attempt in range(max_retries):
        try:
            resp = SESSION.get(url, timeout=REQUEST_TIMEOUT, stream=True)
            resp.raise_for_status()

            # Verify it's actually a PDF
            content_type = resp.headers.get("Content-Type", "")
            if "pdf" not in content_type.lower() and not url.lower().endswith(".pdf"):
                # Check first bytes for PDF magic number
                first_bytes = next(resp.iter_content(chunk_size=5), b"")
                if not first_bytes.startswith(b"%PDF"):
                    logger.warning(f"  Not a PDF: {url}")
                    return False
                # Write the first bytes we already read
                save_path.parent.mkdir(parents=True, exist_ok=True)
                with open(save_path, "wb") as f:
                    f.write(first_bytes)
                    for chunk in resp.iter_content(chunk_size=8192):
                        f.write(chunk)
                return True

            # Download the file
            save_path.parent.mkdir(parents=True, exist_ok=True)
            with open(save_path, "wb") as f:
                for chunk in resp.iter_content(chunk_size=8192):
                    f.write(chunk)
            return True

        except requests.RequestException as e:
            wait_time = (2 ** attempt) * REQUEST_DELAY
            logger.warning(f"  Attempt {attempt + 1} failed for {url}: {e}")
            if attempt < max_retries - 1:
                time.sleep(wait_time)

    return False


def load_metadata() -> list[dict]:
    """Load existing metadata from file."""
    if METADATA_FILE.exists():
        with open(METADATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return []


def save_metadata(metadata: list[dict]):
    """Save metadata to file."""
    METADATA_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(METADATA_FILE, "w", encoding="utf-8") as f:
        json.dump(metadata, f, ensure_ascii=False, indent=2)


def download_all(pdf_list: list[dict]) -> list[dict]:
    """Download all PDFs and update metadata."""
    metadata = load_metadata()
    downloaded_urls = {m["url"] for m in metadata if m.get("downloaded")}

    new_downloads = 0
    skipped = 0
    failed = 0

    for pdf_info in tqdm(pdf_list, desc="Downloading PDFs"):
        url = pdf_info["url"]

        # Skip already downloaded
        if url in downloaded_urls:
            skipped += 1
            continue

        # Determine save path
        category = pdf_info.get("category", "other")
        subfolder = PUBLICATION_SOURCES.get(category, {}).get("subfolder", "other")
        filename = get_filename_from_pdf(pdf_info)
        save_path = PDF_DIR / subfolder / filename

        # Skip if file exists on disk
        if save_path.exists():
            pdf_info["local_path"] = str(save_path)
            pdf_info["downloaded"] = True
            metadata.append(pdf_info)
            downloaded_urls.add(url)
            skipped += 1
            continue

        # Download
        success = download_pdf(url, save_path)
        time.sleep(REQUEST_DELAY)

        if success:
            pdf_info["local_path"] = str(save_path)
            pdf_info["downloaded"] = True
            metadata.append(pdf_info)
            downloaded_urls.add(url)
            new_downloads += 1
        else:
            pdf_info["downloaded"] = False
            metadata.append(pdf_info)
            failed += 1

        # Save metadata periodically
        if (new_downloads + failed) % 10 == 0:
            save_metadata(metadata)

    # Final save
    save_metadata(metadata)

    logger.info(f"Download complete: {new_downloads} new, {skipped} skipped, {failed} failed")
    return metadata
