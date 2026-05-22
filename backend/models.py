"""
models.py – Pydantic schemas used by FastAPI endpoints.
"""
from typing import List, Optional
from pydantic import BaseModel, Field


class ChatMessage(BaseModel):
    role: str = Field(..., description="'user' or 'assistant'")
    content: str


class ChatRequest(BaseModel):
    session_id: str = Field(..., description="Unique session identifier")
    message: str    = Field(..., min_length=1, max_length=4096)
    history: Optional[List[ChatMessage]] = Field(default_factory=list)


class SourceChunk(BaseModel):
    content: str
    source:  str
    score:   float


class ChatResponse(BaseModel):
    session_id: str
    answer:     str
    sources:    List[SourceChunk] = Field(default_factory=list)


class UploadResponse(BaseModel):
    filename:    str
    chunks_added: int
    message:     str


class HealthResponse(BaseModel):
    status:         str
    vector_db_docs: int
    model:          str