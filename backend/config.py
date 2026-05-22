# backend/config.py

"""
Centralized configuration for FinBot.
Loads environment variables and project settings.
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# Load .env variables
load_dotenv()

# -----------------------------------------------------------------------------
# Paths
# -----------------------------------------------------------------------------
BASE_DIR = Path(__file__).resolve().parent.parent

DATA_DIR = BASE_DIR / "data"
CHROMA_DIR = BASE_DIR / "chroma_db"

# Auto-create required directories
DATA_DIR.mkdir(parents=True, exist_ok=True)
CHROMA_DIR.mkdir(parents=True, exist_ok=True)

# -----------------------------------------------------------------------------
# Gemini Configuration
# -----------------------------------------------------------------------------
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")

GEMINI_MODEL = os.getenv(
    "GEMINI_MODEL",
    "gemini-2.5-flash"
)

# -----------------------------------------------------------------------------
# Embedding Model
# -----------------------------------------------------------------------------
EMBEDDING_MODEL = os.getenv(
    "EMBEDDING_MODEL",
    "all-MiniLM-L6-v2"
)

# -----------------------------------------------------------------------------
# RAG Settings
# -----------------------------------------------------------------------------
CHUNK_SIZE = int(
    os.getenv("CHUNK_SIZE", "800")
)

CHUNK_OVERLAP = int(
    os.getenv("CHUNK_OVERLAP", "150")
)

TOP_K = int(
    os.getenv("TOP_K", "5")
)

# -----------------------------------------------------------------------------
# API Settings
# -----------------------------------------------------------------------------
API_HOST = os.getenv(
    "API_HOST",
    "0.0.0.0"
)

API_PORT = int(
    os.getenv("API_PORT", "8000")
)

# -----------------------------------------------------------------------------
# Frontend
# -----------------------------------------------------------------------------
BACKEND_URL = os.getenv(
    "BACKEND_URL",
    f"http://localhost:{API_PORT}"
)

# -----------------------------------------------------------------------------
# Validation
# -----------------------------------------------------------------------------
def validate():
    """
    Ensure required environment variables exist.
    """

    if not GEMINI_API_KEY:
        raise EnvironmentError(
            "GEMINI_API_KEY is missing. "
            "Add it inside your .env file."
        )
    
    
