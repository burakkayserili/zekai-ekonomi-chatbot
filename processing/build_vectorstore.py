"""
Build ChromaDB vector store from processed PDF chunks.
"""

import json
import logging
from pathlib import Path

from tqdm import tqdm
from langchain_chroma import Chroma

from config import PDF_DIR, CHROMA_DIR, METADATA_FILE, COLLECTION_NAME
from processing.pdf_extractor import extract_text_from_pdf
from processing.text_chunker import create_chunks_from_pages
from rag.embeddings import get_embedding_model

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)


def find_all_pdfs() -> list[dict]:
    """Find all downloaded PDFs, using metadata if available."""
    if METADATA_FILE.exists():
        with open(METADATA_FILE, "r", encoding="utf-8") as f:
            metadata = json.load(f)
        # Only return successfully downloaded PDFs
        return [m for m in metadata if m.get("downloaded") and m.get("local_path")]

    # Fallback: scan the PDF directory
    pdfs = []
    for pdf_path in PDF_DIR.rglob("*.pdf"):
        pdfs.append({
            "local_path": str(pdf_path),
            "title": pdf_path.stem,
            "category": pdf_path.parent.name,
            "year": None,
        })
    return pdfs


def build_vectorstore(batch_size: int = 50):
    """
    Process all PDFs and build/update the ChromaDB vector store.
    """
    pdfs = find_all_pdfs()
    if not pdfs:
        logger.warning("No PDFs found. Run the scraper first: python scripts/run_scraper.py")
        return

    logger.info(f"Found {len(pdfs)} PDFs to process")

    # Load embedding model (downloads on first run, ~440MB)
    logger.info("Loading Turkish embedding model (ilk seferde indirme gerekir, ~440MB)...")
    embedding_model = get_embedding_model()

    # Initialize ChromaDB
    CHROMA_DIR.mkdir(parents=True, exist_ok=True)
    vectorstore = Chroma(
        persist_directory=str(CHROMA_DIR),
        embedding_function=embedding_model,
        collection_name=COLLECTION_NAME,
    )

    # Check what's already processed
    existing = vectorstore.get()
    processed_files = set()
    if existing and existing.get("metadatas"):
        for meta in existing["metadatas"]:
            if meta and meta.get("source"):
                processed_files.add(meta["source"])

    all_chunks = []
    processed_count = 0
    skipped_count = 0
    failed_count = 0

    for pdf_info in tqdm(pdfs, desc="Processing PDFs"):
        local_path = pdf_info.get("local_path", "")
        if not local_path or not Path(local_path).exists():
            failed_count += 1
            continue

        # Skip already processed
        source_name = Path(local_path).name
        if source_name in processed_files:
            skipped_count += 1
            continue

        # Extract text
        result = extract_text_from_pdf(local_path)
        if not result["success"]:
            failed_count += 1
            continue

        # Create chunks with metadata
        metadata = {
            "source": source_name,
            "category": pdf_info.get("category", "unknown"),
            "category_name": pdf_info.get("category_name", ""),
            "year": pdf_info.get("year", 0),
            "title": pdf_info.get("title", source_name),
        }

        chunks = create_chunks_from_pages(result["pages"], metadata)
        if chunks:
            all_chunks.extend(chunks)
            processed_count += 1

        # Add to vectorstore in batches
        if len(all_chunks) >= batch_size:
            vectorstore.add_documents(all_chunks)
            logger.info(f"  Added {len(all_chunks)} chunks to vectorstore")
            all_chunks = []

    # Add remaining chunks
    if all_chunks:
        vectorstore.add_documents(all_chunks)
        logger.info(f"  Added {len(all_chunks)} chunks to vectorstore")

    # Report results
    final_count = vectorstore._collection.count()
    logger.info(f"\nVector store build complete:")
    logger.info(f"  Processed: {processed_count} PDFs")
    logger.info(f"  Skipped (already done): {skipped_count}")
    logger.info(f"  Failed: {failed_count}")
    logger.info(f"  Total chunks in store: {final_count}")
    logger.info(f"  Stored at: {CHROMA_DIR}")
