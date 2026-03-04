"""
CLI script to run the full pipeline: scrape, download, process, build vector store.

Usage:
    python scripts/run_all.py
"""

import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from scraper.tcmb_scraper import scrape_all
from scraper.download_pdfs import download_all
from processing.build_vectorstore import build_vectorstore


def main():
    print("=" * 60)
    print("TCMB Economy Chatbot - Full Setup")
    print("=" * 60)

    # Step 1: Scrape
    print("\n[1/3] TCMB web sitesi taranıyor...")
    pdf_list = scrape_all()

    if not pdf_list:
        print("Hiç PDF bulunamadı. İnternet bağlantınızı kontrol edin.")
        return

    print(f"  {len(pdf_list)} PDF bulundu.")

    # Step 2: Download
    print("\n[2/3] PDF'ler indiriliyor...")
    download_all(pdf_list)

    # Step 3: Process & Build Vector Store
    print("\n[3/3] Vektör veritabanı oluşturuluyor...")
    build_vectorstore()

    print("\n" + "=" * 60)
    print("Kurulum tamamlandı! Chatbot'u başlatmak için:")
    print("  streamlit run app.py")
    print("=" * 60)


if __name__ == "__main__":
    main()
