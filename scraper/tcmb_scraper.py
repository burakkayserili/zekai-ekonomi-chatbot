"""
Scrape TCMB website to find all PDF download links from the publications section.
"""

import re
import time
import logging
from urllib.parse import urljoin, urlparse, unquote

import requests
from bs4 import BeautifulSoup

from config import (
    TCMB_BASE_URL, YEAR_START, YEAR_END,
    REQUEST_DELAY, REQUEST_TIMEOUT, USER_AGENT,
)
from scraper.url_registry import PUBLICATION_SOURCES

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

SESSION = requests.Session()
SESSION.headers.update({
    "User-Agent": USER_AGENT,
    "Accept-Language": "tr-TR,tr;q=0.9,en;q=0.8",
})


def fetch_page(url: str) -> BeautifulSoup | None:
    """Fetch a page and return parsed BeautifulSoup, or None on failure."""
    try:
        resp = SESSION.get(url, timeout=REQUEST_TIMEOUT)
        resp.raise_for_status()
        return BeautifulSoup(resp.content, "lxml")
    except requests.RequestException as e:
        logger.warning(f"Failed to fetch {url}: {e}")
        return None


def is_year_in_range(text: str) -> bool:
    """Check if text contains a year within our target range."""
    for year in range(YEAR_START, YEAR_END):
        if str(year) in text:
            return True
    return False


def extract_year_from_text(text: str) -> int | None:
    """Extract a 4-digit year from text if it falls in our range."""
    match = re.search(r"(20[12]\d)", text)
    if match:
        year = int(match.group(1))
        if YEAR_START <= year < YEAR_END:
            return year
    return None


def find_pdf_links(soup: BeautifulSoup, base_url: str) -> list[dict]:
    """Find all PDF links on a page."""
    pdfs = []
    if not soup:
        return pdfs

    for link in soup.find_all("a", href=True):
        href = link["href"]
        # Check for PDF links (direct .pdf or TCMB's WCM download pattern)
        if ".pdf" in href.lower() or "MOD=AJPERES" in href:
            full_url = urljoin(base_url, href)
            title = link.get_text(strip=True) or unquote(href.split("/")[-1])
            pdfs.append({"url": full_url, "title": title})

    return pdfs


def find_subpage_links(soup: BeautifulSoup, base_url: str) -> list[str]:
    """Find links to sub-pages (year pages, detail pages) on a listing page."""
    links = []
    if not soup:
        return links

    for link in soup.find_all("a", href=True):
        href = link["href"]
        full_url = urljoin(base_url, href)
        # Skip external links, anchors, and non-TCMB links
        if full_url.startswith(TCMB_BASE_URL) and "#" not in href:
            links.append(full_url)

    return list(set(links))


def scrape_category(category_key: str, category_info: dict) -> list[dict]:
    """Scrape all PDFs from a single publication category."""
    results = []
    base_path = category_info["path"]
    base_url = TCMB_BASE_URL + base_path
    category_name = category_info["name"]

    logger.info(f"Scraping category: {category_name}")
    logger.info(f"  URL: {base_url}")

    # Fetch the main category page
    soup = fetch_page(base_url)
    if not soup:
        logger.warning(f"  Could not fetch main page for {category_name}")
        return results

    time.sleep(REQUEST_DELAY)

    if category_info.get("has_year_pages"):
        # For categories organized by year, try each year
        for year in range(YEAR_START, YEAR_END):
            year_url = f"{base_url}/{year}"
            logger.info(f"  Checking year page: {year}")
            year_soup = fetch_page(year_url)
            if not year_soup:
                continue
            time.sleep(REQUEST_DELAY)

            # Find PDFs directly on the year page
            pdfs = find_pdf_links(year_soup, year_url)
            for pdf in pdfs:
                pdf["category"] = category_key
                pdf["category_name"] = category_name
                pdf["year"] = year
                results.append(pdf)

            # Also check sub-pages (quarterly reports, issue pages)
            subpages = find_subpage_links(year_soup, year_url)
            for sub_url in subpages:
                # Only follow links that seem to be detail pages under this year
                if str(year) in sub_url and sub_url != year_url:
                    sub_soup = fetch_page(sub_url)
                    if not sub_soup:
                        continue
                    time.sleep(REQUEST_DELAY)

                    sub_pdfs = find_pdf_links(sub_soup, sub_url)
                    for pdf in sub_pdfs:
                        pdf["category"] = category_key
                        pdf["category_name"] = category_name
                        pdf["year"] = year
                        if pdf["url"] not in [r["url"] for r in results]:
                            results.append(pdf)
    else:
        # For flat categories, find PDFs on the main page
        pdfs = find_pdf_links(soup, base_url)
        for pdf in pdfs:
            year = extract_year_from_text(pdf["url"]) or extract_year_from_text(pdf["title"])
            if year and YEAR_START <= year < YEAR_END:
                pdf["category"] = category_key
                pdf["category_name"] = category_name
                pdf["year"] = year
                results.append(pdf)

        # Check sub-pages for more PDFs
        subpages = find_subpage_links(soup, base_url)
        visited = {base_url}

        for sub_url in subpages:
            if sub_url in visited:
                continue
            visited.add(sub_url)

            # Only follow links within the publications section
            if base_path not in sub_url:
                continue

            sub_soup = fetch_page(sub_url)
            if not sub_soup:
                continue
            time.sleep(REQUEST_DELAY)

            sub_pdfs = find_pdf_links(sub_soup, sub_url)
            for pdf in sub_pdfs:
                year = extract_year_from_text(pdf["url"]) or extract_year_from_text(pdf["title"])
                if year and YEAR_START <= year < YEAR_END:
                    pdf["category"] = category_key
                    pdf["category_name"] = category_name
                    pdf["year"] = year
                    if pdf["url"] not in [r["url"] for r in results]:
                        results.append(pdf)

            # Go one level deeper for nested pages
            deeper_pages = find_subpage_links(sub_soup, sub_url)
            for deep_url in deeper_pages:
                if deep_url in visited or base_path not in deep_url:
                    continue
                visited.add(deep_url)

                deep_soup = fetch_page(deep_url)
                if not deep_soup:
                    continue
                time.sleep(REQUEST_DELAY)

                deep_pdfs = find_pdf_links(deep_soup, deep_url)
                for pdf in deep_pdfs:
                    year = extract_year_from_text(pdf["url"]) or extract_year_from_text(pdf["title"])
                    if year and YEAR_START <= year < YEAR_END:
                        pdf["category"] = category_key
                        pdf["category_name"] = category_name
                        pdf["year"] = year
                        if pdf["url"] not in [r["url"] for r in results]:
                            results.append(pdf)

    logger.info(f"  Found {len(results)} PDFs in {category_name}")
    return results


def scrape_all() -> list[dict]:
    """Scrape all publication categories and return a list of PDF metadata."""
    all_pdfs = []

    for key, info in PUBLICATION_SOURCES.items():
        try:
            pdfs = scrape_category(key, info)
            all_pdfs.extend(pdfs)
        except Exception as e:
            logger.error(f"Error scraping {key}: {e}")
            continue

    # Deduplicate by URL
    seen_urls = set()
    unique_pdfs = []
    for pdf in all_pdfs:
        if pdf["url"] not in seen_urls:
            seen_urls.add(pdf["url"])
            unique_pdfs.append(pdf)

    logger.info(f"Total unique PDFs found: {len(unique_pdfs)}")
    return unique_pdfs
