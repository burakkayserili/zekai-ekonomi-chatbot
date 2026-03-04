import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

# Paths
BASE_DIR = Path(__file__).parent
PDF_DIR = BASE_DIR / "data" / "pdfs"
CHROMA_DIR = BASE_DIR / "chroma_db"
METADATA_FILE = BASE_DIR / "data" / "metadata.json"

# TCMB Website
TCMB_BASE_URL = "https://www.tcmb.gov.tr"
TCMB_PUBLICATIONS_URL = TCMB_BASE_URL + "/wps/wcm/connect/TR/TCMB+TR/Main+Menu/Yayinlar/"

# Year range for PDF downloads
YEAR_START = 2020
YEAR_END = 2026  # exclusive, so 2020-2025

# PDF Processing
CHUNK_SIZE = 1000
CHUNK_OVERLAP = 200

# Embedding Model (Turkish-specific, free, local)
EMBEDDING_MODEL = "emrecan/bert-base-turkish-cased-mean-nli-stsb-tr"

# App Password (access control)
APP_PASSWORD = os.getenv("APP_PASSWORD", "")

# LLM (Google Gemini free tier)
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY", "")
LLM_MODEL = "gemini-2.5-flash"
LLM_TEMPERATURE = 0.3
LLM_MAX_TOKENS = 2048

# RAG Settings
TOP_K = 5
COLLECTION_NAME = "tcmb_publications"

# Scraper Settings
REQUEST_DELAY = 2  # seconds between requests
REQUEST_TIMEOUT = 30
USER_AGENT = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"
