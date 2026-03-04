"""
ChromaDB retrieval logic for the RAG pipeline.
"""

from langchain_chroma import Chroma

from config import CHROMA_DIR, COLLECTION_NAME, TOP_K
from rag.embeddings import get_embedding_model


def load_vectorstore() -> Chroma:
    """Load the persisted ChromaDB vector store."""
    embedding_model = get_embedding_model()
    return Chroma(
        persist_directory=str(CHROMA_DIR),
        embedding_function=embedding_model,
        collection_name=COLLECTION_NAME,
    )


def get_retriever(vectorstore: Chroma, top_k: int = TOP_K, filters: dict | None = None):
    """
    Create a retriever from the vector store.

    Args:
        vectorstore: ChromaDB instance
        top_k: Number of chunks to retrieve
        filters: Optional metadata filters (e.g., {"year": 2024})
    """
    search_kwargs = {"k": top_k}
    if filters:
        search_kwargs["filter"] = filters
    return vectorstore.as_retriever(search_kwargs=search_kwargs)
