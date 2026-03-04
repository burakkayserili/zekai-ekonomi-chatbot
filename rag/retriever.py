"""
ChromaDB retrieval logic for the RAG pipeline.
Includes recency-aware retrieval for better results.
"""

from langchain_chroma import Chroma
from langchain_core.documents import Document

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


class RecencyAwareRetriever:
    """
    Custom retriever that fetches extra documents then prioritizes recent ones.
    Fetches 2x documents, sorts by year (newest first), returns top_k.
    """

    def __init__(self, vectorstore: Chroma, top_k: int = TOP_K, filters: dict | None = None):
        self.vectorstore = vectorstore
        self.top_k = top_k
        self.filters = filters

    def invoke(self, query: str) -> list[Document]:
        """Retrieve documents with recency boost."""
        # Fetch 2x more documents than needed
        fetch_k = self.top_k * 2
        search_kwargs = {"k": fetch_k}
        if self.filters:
            search_kwargs["filter"] = self.filters

        retriever = self.vectorstore.as_retriever(search_kwargs=search_kwargs)
        docs = retriever.invoke(query)

        if not docs:
            return docs

        # Sort by year descending (newest first), keep relevance as tiebreaker
        docs_with_index = [(i, doc) for i, doc in enumerate(docs)]
        docs_with_index.sort(
            key=lambda x: (-x[1].metadata.get("year", 0), x[0])
        )

        # Return top_k after recency sort
        return [doc for _, doc in docs_with_index[:self.top_k]]


def get_retriever(vectorstore: Chroma, top_k: int = TOP_K, filters: dict | None = None):
    """
    Create a recency-aware retriever from the vector store.

    Args:
        vectorstore: ChromaDB instance
        top_k: Number of chunks to retrieve
        filters: Optional metadata filters (e.g., {"year": 2024})
    """
    return RecencyAwareRetriever(vectorstore, top_k=top_k, filters=filters)
