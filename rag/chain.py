"""
RAG chain combining Gemini LLM with ChromaDB retriever.
Uses modern LangChain Expression Language (LCEL).
"""

import re
import time
import logging
from datetime import date

from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.output_parsers import StrOutputParser

from config import GOOGLE_API_KEY, LLM_MODEL, LLM_TEMPERATURE, LLM_MAX_TOKENS, TOP_K
from rag.prompts import SYSTEM_PROMPT
from rag.retriever import load_vectorstore, get_retriever
from rag.source_utils import get_readable_source

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
    """Format retrieved documents into a single context string with readable metadata."""
    parts = []
    for doc in docs:
        meta = doc.metadata
        source_file = meta.get('source', '?')
        category = meta.get('category_name', '?')
        year = meta.get('year', '?')
        readable = get_readable_source(source_file, category, year).replace("📄 ", "")
        header = f"[Kaynak: {readable}]"
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

    def _detect_category(self, question: str) -> str | None:
        """Detect if user is asking about a specific TCMB publication category."""
        q = question.lower()
        if "enflasyon rapor" in q:
            return "enflasyon_raporu"
        if "finansal istikrar" in q:
            return "finansal_istikrar"
        if "fiyat gelişme" in q or "aylık fiyat" in q:
            return "aylik_fiyat"
        if "para politika" in q:
            return "para_politikasi"
        return None

    def _detect_recency(self, question: str) -> int | None:
        """
        Detect if user is asking about recent data.
        Returns number of years to look back, or None if not a recency query.

        Examples:
            "en güncel rapor" → 2 (last 2 years)
            "son 3 yılda" → 3
            "son 5 yıldaki" → 5
        """
        q = question.lower()

        # Pattern: "son X yıl" → extract X
        m = re.search(r'son\s+(\d+)\s+yıl', q)
        if m:
            return int(m.group(1))

        # Keywords for "most recent" → default 2 years
        recency_keywords = [
            "en güncel", "en son", "en yeni", "son rapor",
            "güncel rapor", "son yayın", "en yakın",
            "şu anki", "mevcut", "son dönem",
        ]
        if any(kw in q for kw in recency_keywords):
            return 2

        return None

    def _merge_filters(self, filters: dict | None, extra: dict) -> dict:
        """Merge extra filter conditions into existing filters."""
        if not filters:
            return extra
        # Combine with $and
        conditions = []
        if "$and" in filters:
            conditions.extend(filters["$and"])
        else:
            conditions.append(filters)
        conditions.append(extra)
        return {"$and": conditions}

    def query(self, question: str, filters: dict | None = None) -> dict:
        """
        Query with source document tracking and dynamic filters.

        Args:
            question: User's question
            filters: Optional metadata filters (year, category)
        """
        # Auto-detect category from question
        detected_cat = self._detect_category(question)
        if detected_cat:
            filters = self._merge_filters(filters, {"category": detected_cat})

        # Auto-detect recency: filter to relevant years
        lookback = self._detect_recency(question)
        if lookback:
            current_year = date.today().year
            recent_years = list(range(current_year - lookback + 1, current_year + 1))
            filters = self._merge_filters(filters, {"year": {"$in": recent_years}})

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
