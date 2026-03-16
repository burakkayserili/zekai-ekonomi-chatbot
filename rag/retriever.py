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
    Fetches 3x documents, scores by relevance + recency, returns top_k.
    """

    def __init__(self, vectorstore: Chroma, top_k: int = TOP_K, filters: dict | None = None):
        self.vectorstore = vectorstore
        self.top_k = top_k
        self.filters = filters

    def invoke(self, query: str) -> list[Document]:
        """Retrieve documents with recency boost."""
        # Fetch 3x more documents than needed for better reranking
        fetch_k = self.top_k * 3
        search_kwargs = {"k": fetch_k}
        if self.filters:
            search_kwargs["filter"] = self.filters

        # Use similarity_search_with_relevance_scores for scoring
        filter_arg = self.filters if self.filters else {}
        try:
            results = self.vectorstore.similarity_search_with_relevance_scores(
                query, k=fetch_k, filter=filter_arg if filter_arg else None
            )
        except Exception:
            # Fallback to basic retriever
            retriever = self.vectorstore.as_retriever(search_kwargs=search_kwargs)
            docs = retriever.invoke(query)
            if not docs:
                return docs
            docs.sort(key=lambda d: -d.metadata.get("year", 0))
            return docs[:self.top_k]

        if not results:
            return []

        # Find the max year in results for normalization
        max_year = max(doc.metadata.get("year", 2020) for doc, _ in results)
        min_year = min(doc.metadata.get("year", 2020) for doc, _ in results)
        year_range = max(max_year - min_year, 1)

        # Combined score: relevance (0-1) + recency bonus (0-0.3)
        scored = []
        for doc, relevance_score in results:
            year = doc.metadata.get("year", 2020)
            recency_bonus = 0.3 * (year - min_year) / year_range
            combined = relevance_score + recency_bonus
            scored.append((combined, doc))

        # Sort by combined score descending
        scored.sort(key=lambda x: -x[0])

        return [doc for _, doc in scored[:self.top_k]]


def get_retriever(vectorstore: Chroma, top_k: int = TOP_K, filters: dict | None = None):
    """
    Create a recency-aware retriever from the vector store.

    Args:
        vectorstore: ChromaDB instance
        top_k: Number of chunks to retrieve
        filters: Optional metadata filters (e.g., {"year": 2024})
    """
    return RecencyAwareRetriever(vectorstore, top_k=top_k, filters=filters)
