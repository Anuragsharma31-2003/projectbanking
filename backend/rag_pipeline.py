"""
rag_pipeline.py – Full RAG engine:
    • ChromaDB for vector storage
    • Sentence-Transformers for local embeddings (no API cost)
    • LangChain text splitter
    • Gemini 1.5 Flash for generation
    • Cross-encoder reranker (bonus)
"""
from __future__ import annotations

import logging
import re
from pathlib import Path
from typing import List, Tuple

import chromadb
import google.generativeai as genai
from google.api_core import exceptions as google_exceptions
from chromadb.config import Settings
from langchain.text_splitter import RecursiveCharacterTextSplitter
from sentence_transformers import CrossEncoder, SentenceTransformer

from . import config
from .models import SourceChunk

logger = logging.getLogger(__name__)

# ── Singleton initialisation ───────────────────────────────────────────────────

_embedder:      SentenceTransformer | None = None
_reranker:      CrossEncoder | None        = None
_chroma_client: chromadb.Client | None     = None
_collection:    chromadb.Collection | None = None


def _get_embedder() -> SentenceTransformer:
    global _embedder
    if _embedder is None:
        logger.info("Loading embedding model: %s", config.EMBEDDING_MODEL)
        _embedder = SentenceTransformer(config.EMBEDDING_MODEL)
    return _embedder


def _get_reranker() -> CrossEncoder:
    global _reranker
    if _reranker is None:
        logger.info("Loading cross-encoder reranker …")
        _reranker = CrossEncoder("cross-encoder/ms-marco-MiniLM-L-6-v2")
    return _reranker


def _get_collection() -> chromadb.Collection:
    global _chroma_client, _collection
    if _collection is None:
        config.CHROMA_DIR.mkdir(parents=True, exist_ok=True)
        _chroma_client = chromadb.PersistentClient(
            path=str(config.CHROMA_DIR),
            settings=Settings(anonymized_telemetry=False),
        )
        _collection = _chroma_client.get_or_create_collection(
            name="banking_docs",
            metadata={"hnsw:space": "cosine"},
        )
        logger.info("ChromaDB collection loaded — %d docs", _collection.count())
    return _collection


def _configure_gemini():
    config.validate()
    genai.configure(api_key=config.GEMINI_API_KEY)


def _raise_gemini_config_error(exc: Exception):
    message = str(exc)
    if "API_KEY_INVALID" in message or "API key not valid" in message:
        raise EnvironmentError(
            "GEMINI_API_KEY is invalid. Add a valid Gemini API key to your .env file "
            "and restart the backend."
        ) from exc
    if "is not found for API version" in message or "is not supported for generateContent" in message:
        raise EnvironmentError(
            f"GEMINI_MODEL={config.GEMINI_MODEL!r} is not available for generateContent. "
            "Set GEMINI_MODEL to a supported text model such as 'gemini-2.5-flash' "
            "and restart the backend."
        ) from exc
    raise exc


# ── Document ingestion ─────────────────────────────────────────────────────────

def ingest_text(text: str, source: str) -> int:
    """Chunk text and upsert into ChromaDB. Returns number of chunks added."""
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=config.CHUNK_SIZE,
        chunk_overlap=config.CHUNK_OVERLAP,
        separators=["\n\n", "\n", ".", " ", ""],
    )
    chunks = splitter.split_text(text)
    if not chunks:
        return 0

    collection = _get_collection()
    embedder   = _get_embedder()

    embeddings = embedder.encode(chunks, show_progress_bar=False).tolist()
    ids        = [f"{source}_{i}" for i in range(len(chunks))]
    metadatas  = [{"source": source} for _ in chunks]

    collection.upsert(
        ids=ids,
        documents=chunks,
        embeddings=embeddings,
        metadatas=metadatas,
    )
    logger.info("Ingested %d chunks from '%s'", len(chunks), source)
    return len(chunks)


def ingest_file(file_path: Path) -> int:
    """Load a PDF or TXT file and ingest its content."""
    suffix = file_path.suffix.lower()

    if suffix == ".pdf":
        import pypdf
        reader = pypdf.PdfReader(str(file_path))
        text   = "\n\n".join(page.extract_text() or "" for page in reader.pages)
    elif suffix in (".txt", ".md"):
        text = file_path.read_text(encoding="utf-8", errors="ignore")
    else:
        raise ValueError(f"Unsupported file type: {suffix}")

    return ingest_text(text, source=file_path.name)


# ── Retrieval ──────────────────────────────────────────────────────────────────

def retrieve(query: str, top_k: int | None = None) -> List[SourceChunk]:
    """Embed query → similarity search → cross-encoder rerank → return top_k."""
    k          = top_k or config.TOP_K
    collection = _get_collection()
    embedder   = _get_embedder()

    if collection.count() == 0:
        return []

    q_embedding = embedder.encode([query], show_progress_bar=False).tolist()
    results     = collection.query(
        query_embeddings=q_embedding,
        n_results=min(k * 3, collection.count()),   # over-fetch for reranking
        include=["documents", "metadatas", "distances"],
    )

    docs      = results["documents"][0]
    metas     = results["metadatas"][0]
    distances = results["distances"][0]

    if not docs:
        return []

    # Rerank with cross-encoder (bonus feature)
    reranker = _get_reranker()
    pairs    = [[query, doc] for doc in docs]
    scores   = reranker.predict(pairs)

    ranked: List[Tuple[float, str, str]] = sorted(
        zip(scores, docs, [m.get("source", "unknown") for m in metas]),
        key=lambda x: x[0],
        reverse=True,
    )[:k]

    return [
        SourceChunk(content=doc, source=src, score=float(score))
        for score, doc, src in ranked
    ]


# ── Generation ────────────────────────────────────────────────────────────────

SYSTEM_PROMPT = """You are FinBot, an expert AI banking assistant for a leading fintech company.

Your role is to help customers with:
- Loan queries (personal loans, home loans, auto loans)
- Credit card information and policies
- Banking FAQs and procedures
- Account services and support

Guidelines:
1. Answer ONLY from the retrieved context provided. If the context doesn't contain enough information, say so clearly.
2. Be concise, factual, and professional.
3. Use numbered lists or bullet points for multi-step answers.
4. Never invent interest rates, fees, or policy details not present in context.
5. Maintain conversational context — refer to what was discussed earlier in the session.
6. If a query is completely unrelated to banking, politely redirect.
"""


def generate_answer(
    query:   str,
    chunks:  List[SourceChunk],
    history: List[dict] | None = None,
) -> str:
    _configure_gemini()
    model = genai.GenerativeModel(
        model_name=config.GEMINI_MODEL,
        system_instruction=SYSTEM_PROMPT,
    )

    # Build context block
    if chunks:
        context_block = "\n\n---\n\n".join(
            f"[Source: {c.source}]\n{c.content}" for c in chunks
        )
        context_section = f"RETRIEVED CONTEXT:\n{context_block}\n\n"
    else:
        context_section = "RETRIEVED CONTEXT: No relevant documents found.\n\n"

    # Build conversation history string
    history_text = ""
    if history:
        lines = []
        for msg in history[-6:]:          # last 6 turns to stay within context
            role  = "Customer" if msg["role"] == "user" else "FinBot"
            lines.append(f"{role}: {msg['content']}")
        history_text = "CONVERSATION HISTORY:\n" + "\n".join(lines) + "\n\n"

    full_prompt = (
        f"{history_text}"
        f"{context_section}"
        f"Customer question: {query}\n\n"
        "Answer:"
    )

    try:
        response = model.generate_content(full_prompt)
    except google_exceptions.GoogleAPICallError as exc:
        _raise_gemini_config_error(exc)
    return response.text.strip()


# ── Streaming generation ───────────────────────────────────────────────────────

def generate_answer_stream(
    query:   str,
    chunks:  List[SourceChunk],
    history: List[dict] | None = None,
):
    """Yields text tokens for streaming responses (bonus feature)."""
    _configure_gemini()
    model = genai.GenerativeModel(
        model_name=config.GEMINI_MODEL,
        system_instruction=SYSTEM_PROMPT,
    )

    if chunks:
        context_block = "\n\n---\n\n".join(
            f"[Source: {c.source}]\n{c.content}" for c in chunks
        )
        context_section = f"RETRIEVED CONTEXT:\n{context_block}\n\n"
    else:
        context_section = "RETRIEVED CONTEXT: No relevant documents found.\n\n"

    history_text = ""
    if history:
        lines = []
        for msg in history[-6:]:
            role = "Customer" if msg["role"] == "user" else "FinBot"
            lines.append(f"{role}: {msg['content']}")
        history_text = "CONVERSATION HISTORY:\n" + "\n".join(lines) + "\n\n"

    full_prompt = (
        f"{history_text}"
        f"{context_section}"
        f"Customer question: {query}\n\n"
        "Answer:"
    )

    try:
        stream = model.generate_content(full_prompt, stream=True)
        for chunk in stream:
            if chunk.text:
                yield chunk.text
    except google_exceptions.GoogleAPICallError as exc:
        _raise_gemini_config_error(exc)


# ── Utility ───────────────────────────────────────────────────────────────────

def get_collection_count() -> int:
    try:
        return _get_collection().count()
    except Exception:
        return 0
