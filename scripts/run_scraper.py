"""
CLI script to scrape and download PDFs from TCMB website.

Usage:
    python scripts/run_scraper.py
"""

import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from scraper.tcmb_scraper import scrape_all
from scraper.download_pdfs import download_all


def main():
    print("=" * 60)
    print("TCMB PDF Scraper")
    print("=" * 60)

    # Step 1: Find PDF links
    print("\n[1/2] TCMB web sitesi taranıyor...")
    pdf_list = scrape_all()

    if not pdf_list:
        print("Hiç PDF bulunamadı. İnternet bağlantınızı kontrol edin.")
        return

    print(f"\n{len(pdf_list)} PDF bulundu.")

    # Step 2: Download PDFs
    print("\n[2/2] PDF'ler indiriliyor...")
    metadata = download_all(pdf_list)

    downloaded = sum(1 for m in metadata if m.get("downloaded"))
    print(f"\nTamamlandı! {downloaded} PDF indirildi.")
    print(f"PDF'ler burada: data/pdfs/")


if __name__ == "__main__":
    main()
