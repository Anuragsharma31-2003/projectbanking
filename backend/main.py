"""
main.py – FastAPI backend exposing /chat, /chat/stream, /upload, /health
Run:  uvicorn main:app --host 0.0.0.0 --port 8000 --reload
"""
import logging
import shutil
import tempfile
import uuid
from pathlib import Path
from typing import Dict, List

from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse

from . import config
from . import rag_pipeline as rag
from .models import (
    ChatRequest,
    ChatResponse,
    HealthResponse,
    SourceChunk,
    UploadResponse,
)

logging.basicConfig(level=logging.INFO, format="%(levelname)s | %(name)s | %(message)s")
logger = logging.getLogger(__name__)

# ── App ───────────────────────────────────────────────────────────────────────
app = FastAPI(
    title="FinBot Banking Chatbot API",
    description="RAG-powered banking support chatbot backend",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],           # tighten in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── In-memory session store ───────────────────────────────────────────────────
# Maps session_id → list of {"role": str, "content": str}
_sessions: Dict[str, List[dict]] = {}


# ── Startup: load default documents ───────────────────────────────────────────
@app.on_event("startup")
async def startup_event():
    logger.info("FinBot API starting …")
    doc_count = rag.get_collection_count()
    if doc_count == 0:
        logger.info("No documents in vector DB — ingesting default banking docs …")
        default_docs = config.DATA_DIR
        if default_docs.exists():
            for fpath in default_docs.iterdir():
                if fpath.suffix.lower() in (".pdf", ".txt", ".md"):
                    try:
                        n = rag.ingest_file(fpath)
                        logger.info("Ingested %d chunks from %s", n, fpath.name)
                    except Exception as exc:
                        logger.warning("Failed to ingest %s: %s", fpath.name, exc)
        else:
            logger.warning("Data directory not found: %s", default_docs)
    else:
        logger.info("Vector DB ready with %d document chunks.", doc_count)


# ── Routes ────────────────────────────────────────────────────────────────────

@app.get("/health", response_model=HealthResponse, tags=["System"])
async def health():
    """Liveness & readiness probe."""
    return HealthResponse(
        status="ok",
        vector_db_docs=rag.get_collection_count(),
        model=config.GEMINI_MODEL,
    )


@app.post("/chat", response_model=ChatResponse, tags=["Chat"])
async def chat(req: ChatRequest):
    """
    Non-streaming chat endpoint.
    Accepts a message + optional client-side history.
    Maintains server-side session history for context retention.
    """
    if not req.message.strip():
        raise HTTPException(status_code=422, detail="Message cannot be empty.")

    # Merge/init session history
    session_history = _sessions.setdefault(req.session_id, [])
    if req.history:
        # Client sent its own history (Streamlit) — use it as source of truth
        session_history = [{"role": m.role, "content": m.content} for m in req.history]
        _sessions[req.session_id] = session_history

    try:
        # 1. Retrieve relevant chunks
        chunks: List[SourceChunk] = rag.retrieve(req.message)

        # 2. Generate answer
        answer = rag.generate_answer(req.message, chunks, history=session_history)

        # 3. Update session
        session_history.append({"role": "user",      "content": req.message})
        session_history.append({"role": "assistant",  "content": answer})
        # Keep last 20 turns to cap memory usage
        _sessions[req.session_id] = session_history[-20:]

        return ChatResponse(
            session_id=req.session_id,
            answer=answer,
            sources=chunks,
        )

    except EnvironmentError as exc:
        raise HTTPException(status_code=503, detail=str(exc))
    except Exception as exc:
        logger.exception("Chat error: %s", exc)
        raise HTTPException(status_code=500, detail="Internal error — please try again.")


@app.post("/chat/stream", tags=["Chat"])
async def chat_stream(req: ChatRequest):
    """
    Streaming chat endpoint (bonus feature).
    Returns a text/event-stream response.
    """
    if not req.message.strip():
        raise HTTPException(status_code=422, detail="Message cannot be empty.")

    session_history = _sessions.setdefault(req.session_id, [])
    if req.history:
        session_history = [{"role": m.role, "content": m.content} for m in req.history]
        _sessions[req.session_id] = session_history

    chunks = rag.retrieve(req.message)
    full_answer = []

    def event_generator():
        try:
            for token in rag.generate_answer_stream(req.message, chunks, history=session_history):
                full_answer.append(token)
                yield f"data: {token}\n\n"
        finally:
            answer = "".join(full_answer)
            session_history.append({"role": "user",     "content": req.message})
            session_history.append({"role": "assistant", "content": answer})
            _sessions[req.session_id] = session_history[-20:]
            yield "data: [DONE]\n\n"

    return StreamingResponse(event_generator(), media_type="text/event-stream")


@app.post("/upload", response_model=UploadResponse, tags=["Documents"])
async def upload_document(file: UploadFile = File(...)):
    """
    Upload a PDF or TXT document to be ingested into the vector DB.
    """
    allowed = {".pdf", ".txt", ".md"}
    suffix  = Path(file.filename).suffix.lower()
    if suffix not in allowed:
        raise HTTPException(
            status_code=415,
            detail=f"Unsupported file type '{suffix}'. Allowed: {', '.join(allowed)}",
        )

    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        shutil.copyfileobj(file.file, tmp)
        tmp_path = Path(tmp.name)

    try:
        n = rag.ingest_file(tmp_path)
        return UploadResponse(
            filename=file.filename,
            chunks_added=n,
            message=f"Successfully ingested {n} chunks from '{file.filename}'.",
        )
    except Exception as exc:
        logger.exception("Upload error: %s", exc)
        raise HTTPException(status_code=500, detail=f"Ingestion failed: {exc}")
    finally:
        tmp_path.unlink(missing_ok=True)


@app.delete("/session/{session_id}", tags=["System"])
async def clear_session(session_id: str):
    """Clear conversation history for a given session."""
    _sessions.pop(session_id, None)
    return {"message": f"Session '{session_id}' cleared."}
