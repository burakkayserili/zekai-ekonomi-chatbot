"""
RAG chain combining Gemini LLM with ChromaDB retriever.
Uses modern LangChain Expression Language (LCEL).
"""

import time
import logging
from datetime import date

from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.output_parsers import StrOutputParser

from config import GOOGLE_API_KEY, LLM_MODEL, LLM_TEMPERATURE, LLM_MAX_TOKENS, TOP_K
from rag.prompts import SYSTEM_PROMPT
from rag.retriever import load_vectorstore, get_retriever

logger = logging.getLogger(__name__)


def create_llm():
    """Create the Google Gemini LLM instance."""
    if not GOOGLE_API_KEY:
        raise ValueError(
            "GOOGLE_API_KEY bulunamadı! Lütfen .env dosyasına API anahtarınızı ekleyin.\n"
            "Ücretsiz API anahtarı almak için: https://aistudio.google.com/"
        )
    return ChatGoogleGenerativeAI(
        model=LLM_MODEL,
        google_api_key=GOOGLE_API_KEY,
        temperature=LLM_TEMPERATURE,
        max_output_tokens=LLM_MAX_TOKENS,
    )


def format_docs(docs):
    """Format retrieved documents into a single context string with metadata."""
    parts = []
    for doc in docs:
        meta = doc.metadata
        header = f"[Kaynak: {meta.get('title', meta.get('source', '?'))} | Yıl: {meta.get('year', '?')} | Kategori: {meta.get('category_name', '?')}]"
        parts.append(f"{header}\n{doc.page_content}")
    return "\n\n---\n\n".join(parts)


class RAGChain:
    """RAG chain with conversation history, source tracking, and dynamic filters."""

    def __init__(self):
        self.llm = create_llm()
        self.vectorstore = load_vectorstore()
        self.chat_history: list[tuple[str, str]] = []
        self._last_source_docs = []

        # Build the prompt
        self.prompt = ChatPromptTemplate.from_messages([
            ("system", SYSTEM_PROMPT),
            MessagesPlaceholder(variable_name="chat_history", optional=True),
            ("human", "{question}"),
        ])

    def _get_history_messages(self):
        """Get recent chat history as message tuples."""
        from langchain_core.messages import HumanMessage, AIMessage
        messages = []
        # Keep last 5 exchanges
        for human, ai in self.chat_history[-5:]:
            messages.append(HumanMessage(content=human))
            messages.append(AIMessage(content=ai))
        return messages

    def query(self, question: str, filters: dict | None = None) -> dict:
        """
        Query with source document tracking and dynamic filters.

        Args:
            question: User's question
            filters: Optional metadata filters (year, category)
        """
        # Create retriever with current filters
        retriever = get_retriever(self.vectorstore, filters=filters)

        # Get source documents
        self._last_source_docs = retriever.invoke(question)

        # Build context
        context = format_docs(self._last_source_docs)

        # Build prompt with context and current date
        today = date.today()
        months_tr = {1: "Ocak", 2: "Şubat", 3: "Mart", 4: "Nisan", 5: "Mayıs", 6: "Haziran",
                     7: "Temmuz", 8: "Ağustos", 9: "Eylül", 10: "Ekim", 11: "Kasım", 12: "Aralık"}
        today_str = f"{today.day} {months_tr[today.month]} {today.year}"
        messages = self.prompt.invoke({
            "context": context,
            "question": question,
            "today": today_str,
            "chat_history": self._get_history_messages(),
        })

        # Get LLM response
        response = self.llm.invoke(messages)
        answer = response.content

        # Update history
        self.chat_history.append((question, answer))

        return {
            "answer": answer,
            "source_documents": self._last_source_docs,
        }


def create_rag_chain() -> RAGChain:
    """Create the full RAG chain."""
    return RAGChain()


def query_chain(chain: RAGChain, question: str, filters: dict | None = None, max_retries: int = 3) -> dict:
    """
    Query the RAG chain with retry logic for rate limits.

    Args:
        chain: RAGChain instance
        question: User's question
        filters: Optional metadata filters
        max_retries: Number of retry attempts

    Returns:
        dict with 'answer' and 'source_documents'
    """
    for attempt in range(max_retries):
        try:
            return chain.query(question, filters=filters)
        except Exception as e:
            error_msg = str(e).lower()
            if "quota" in error_msg or "rate" in error_msg or "resource" in error_msg:
                wait_time = (2 ** attempt) * 5
                logger.warning(f"Rate limit, {wait_time}s bekleniyor...")
                time.sleep(wait_time)
            else:
                logger.error(f"Query error: {e}")
                return {
                    "answer": f"Bir hata oluştu: {e}",
                    "source_documents": [],
                }

    return {
        "answer": "API istek limiti aşıldı. Lütfen birkaç dakika bekleyip tekrar deneyin.",
        "source_documents": [],
    }
