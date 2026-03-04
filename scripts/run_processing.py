"""
CLI script to process downloaded PDFs and build the vector store.

Usage:
    python scripts/run_processing.py
"""

import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from processing.build_vectorstore import build_vectorstore


def main():
    print("=" * 60)
    print("TCMB PDF Processing & Vector Store Builder")
    print("=" * 60)

    print("\nPDF'ler işleniyor ve vektör veritabanı oluşturuluyor...")
    print("(İlk çalıştırmada embedding modeli indirilecek, ~440MB)\n")

    build_vectorstore()

    print("\nTamamlandı! Şimdi chatbot'u başlatabilirsiniz:")
    print("  streamlit run app.py")


if __name__ == "__main__":
    main()
