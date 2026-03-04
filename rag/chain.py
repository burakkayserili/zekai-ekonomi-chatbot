"""
RAG chain combining Gemini LLM with ChromaDB retriever.
Uses modern LangChain Expression Language (LCEL).
"""

import time
import logging

from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough

from config import GOOGLE_API_KEY, LLM_MODEL, LLM_TEMPERATURE, LLM_MAX_TOKENS
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
    """Format retrieved documents into a single context string."""
    return "\n\n---\n\n".join(doc.page_content for doc in docs)


class RAGChain:
    """RAG chain with conversation history and source tracking."""

    def __init__(self, filters: dict | None = None):
        self.llm = create_llm()
        self.vectorstore = load_vectorstore()
        self.retriever = get_retriever(self.vectorstore, filters=filters)
        self.chat_history: list[tuple[str, str]] = []
        self._last_source_docs = []

        # Build the prompt
        self.prompt = ChatPromptTemplate.from_messages([
            ("system", SYSTEM_PROMPT),
            MessagesPlaceholder(variable_name="chat_history", optional=True),
            ("human", "{question}"),
        ])

        # Build the chain
        self.chain = (
            {
                "context": self.retriever | format_docs,
                "question": RunnablePassthrough(),
                "chat_history": lambda _: self._get_history_messages(),
            }
            | self.prompt
            | self.llm
            | StrOutputParser()
        )

    def _get_history_messages(self):
        """Get recent chat history as message tuples."""
        from langchain_core.messages import HumanMessage, AIMessage
        messages = []
        # Keep last 5 exchanges
        for human, ai in self.chat_history[-5:]:
            messages.append(HumanMessage(content=human))
            messages.append(AIMessage(content=ai))
        return messages

    def query(self, question: str) -> dict:
        """Query with source document tracking."""
        # Get source documents separately
        self._last_source_docs = self.retriever.invoke(question)

        # Run the chain
        answer = self.chain.invoke(question)

        # Update history
        self.chat_history.append((question, answer))

        return {
            "answer": answer,
            "source_documents": self._last_source_docs,
        }


def create_rag_chain(filters: dict | None = None) -> RAGChain:
    """Create the full RAG chain."""
    return RAGChain(filters=filters)


def query_chain(chain: RAGChain, question: str, max_retries: int = 3) -> dict:
    """
    Query the RAG chain with retry logic for rate limits.

    Returns:
        dict with 'answer' and 'source_documents'
    """
    for attempt in range(max_retries):
        try:
            return chain.query(question)
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
