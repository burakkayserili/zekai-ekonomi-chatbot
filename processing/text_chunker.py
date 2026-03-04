"""
Split extracted PDF text into chunks for embedding and retrieval.
"""

from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.documents import Document

from config import CHUNK_SIZE, CHUNK_OVERLAP


def create_chunks(
    text: str,
    metadata: dict,
    chunk_size: int = CHUNK_SIZE,
    chunk_overlap: int = CHUNK_OVERLAP,
) -> list[Document]:
    """
    Split text into overlapping chunks with metadata.

    Args:
        text: Full text from a PDF
        metadata: Dict with source, category, year, etc.
        chunk_size: Max characters per chunk
        chunk_overlap: Overlap between consecutive chunks

    Returns:
        List of LangChain Document objects
    """
    if not text or not text.strip():
        return []

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        separators=["\n\n", "\n", ". ", ", ", " ", ""],
        length_function=len,
    )

    chunks = splitter.split_text(text)

    documents = []
    for i, chunk in enumerate(chunks):
        chunk = chunk.strip()
        if not chunk or len(chunk) < 50:
            continue

        doc_metadata = {
            **metadata,
            "chunk_index": i,
            "chunk_total": len(chunks),
        }
        documents.append(Document(page_content=chunk, metadata=doc_metadata))

    return documents


def create_chunks_from_pages(
    pages: list[dict],
    metadata: dict,
    chunk_size: int = CHUNK_SIZE,
    chunk_overlap: int = CHUNK_OVERLAP,
) -> list[Document]:
    """
    Split text page by page, preserving page number in metadata.
    """
    all_documents = []

    for page in pages:
        page_text = page.get("text", "")
        page_num = page.get("page_num", 0)

        if not page_text or len(page_text.strip()) < 50:
            continue

        page_metadata = {**metadata, "page": page_num}
        docs = create_chunks(page_text, page_metadata, chunk_size, chunk_overlap)
        all_documents.extend(docs)

    return all_documents
