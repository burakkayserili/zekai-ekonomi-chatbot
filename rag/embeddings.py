"""
Turkish embedding model wrapper for the RAG pipeline.
"""

import platform

from langchain_huggingface import HuggingFaceEmbeddings

from config import EMBEDDING_MODEL


def get_embedding_model() -> HuggingFaceEmbeddings:
    """
    Load the Turkish sentence-transformer embedding model.
    Auto-detects Apple Silicon for GPU acceleration.
    First run downloads the model (~440MB, one-time).
    """
    # Auto-detect device
    device = "cpu"
    if platform.system() == "Darwin" and platform.processor() == "arm":
        device = "mps"  # Apple Silicon GPU

    return HuggingFaceEmbeddings(
        model_name=EMBEDDING_MODEL,
        model_kwargs={"device": device},
        encode_kwargs={"normalize_embeddings": True},
    )
