# FinBot Banking RAG Chatbot

FinBot is an AI banking assistant built with Retrieval-Augmented Generation (RAG). It answers banking questions from uploaded or preloaded documents using semantic search, ChromaDB, Sentence Transformers, a FastAPI backend, Gemini, and a Streamlit frontend.

## Live Demo

- Frontend: https://projectbankinganurag.streamlit.app/
- Backend API: https://projectbanking-api.onrender.com
- Backend Health Check: https://projectbanking-api.onrender.com/health
- Backend Swagger Docs: https://projectbanking-api.onrender.com/docs
- GitHub Repository: https://github.com/Anuragsharma31-2003/projectbanking

![Project Screenshot](image.png)

## Features

- Banking-focused RAG chatbot
- PDF, TXT, and Markdown document ingestion
- ChromaDB vector database
- Sentence Transformers embeddings with `all-MiniLM-L6-v2`
- Cross-encoder reranking for better retrieval quality
- Gemini-powered response generation
- FastAPI backend with Swagger docs
- Streamlit frontend
- Source attribution for retrieved chunks
- Session-based conversational memory
- Runtime document upload support

## Tech Stack

| Layer | Tools |
| --- | --- |
| Frontend | Streamlit, Requests |
| Backend | FastAPI, Uvicorn, Pydantic |
| RAG | LangChain text splitter, ChromaDB |
| Embeddings | Sentence Transformers, PyTorch |
| LLM | Google Gemini API |
| Deployment | Streamlit Community Cloud, Render |

## Architecture

```text
Banking PDFs / TXT / MD
        |
        v
Document ingestion
        |
        v
Chunking + embeddings
        |
        v
ChromaDB vector store
        |
        v
Semantic retrieval + reranking
        |
        v
Gemini response generation
        |
        v
Streamlit chat UI
```

## Project Structure

```text
banking-rag-chatbot/
├── backend/
│   ├── __init__.py
│   ├── config.py
│   ├── ingest.py
│   ├── main.py
│   ├── models.py
│   ├── rag_pipeline.py
│   └── requirements.txt
├── data/
│   └── sample banking documents
├── frontend/
│   └── app.py
├── .env.example
├── .gitignore
├── .python-version
├── image.png
├── README.md
├── render.yaml
└── requirements.txt
```

## Local Setup

Use Python 3.11 for the backend.

```powershell
git clone https://github.com/Anuragsharma31-2003/projectbanking.git
cd projectbanking

py -3.11 -m venv venv
.\venv\Scripts\Activate.ps1

python -m pip install --upgrade pip setuptools wheel
python -m pip install -r backend\requirements.txt
```

Create `.env` from `.env.example`:

```env
GEMINI_API_KEY=your_gemini_api_key_here
GEMINI_MODEL=gemini-2.5-flash
```

Ingest documents:

```powershell
python -m backend.ingest
```

Run the backend:

```powershell
uvicorn backend.main:app --reload
```

Run the frontend in another terminal:

```powershell
streamlit run frontend\app.py
```

Local URLs:

- Frontend: http://localhost:8501
- Backend: http://localhost:8000
- API Docs: http://localhost:8000/docs

## API Endpoints

| Method | Endpoint | Description |
| --- | --- | --- |
| `GET` | `/health` | Backend status and vector document count |
| `POST` | `/chat` | Non-streaming chat response |
| `POST` | `/chat/stream` | Streaming chat response |
| `POST` | `/upload` | Upload and ingest a document |
| `DELETE` | `/session/{session_id}` | Clear a chat session |

## Deployment

### Backend On Render

The backend is deployed on Render using `render.yaml`.

Render service:

```text
https://projectbanking-api.onrender.com
```

Required Render environment variable:

```env
GEMINI_API_KEY=your_real_gemini_api_key
```

Render automatically uses:

```text
Start command: uvicorn backend.main:app --host 0.0.0.0 --port $PORT
Health path: /health
Python version: 3.11.9
```

### Frontend On Streamlit Community Cloud

The frontend is deployed on Streamlit Community Cloud:

```text
https://projectbankinganurag.streamlit.app/
```

Streamlit app settings:

```text
Repository: Anuragsharma31-2003/projectbanking
Branch: main
Main file path: frontend/app.py
Python version: 3.12
```

Streamlit secret:

```toml
BACKEND_URL = "https://projectbanking-api.onrender.com"
```

Only the backend needs `GEMINI_API_KEY`. The frontend should only know `BACKEND_URL`.

## Example Questions

- What are the credit card eligibility criteria?
- What documents are required for a home loan?
- What are the credit card late payment charges?
- Explain RBI banking regulations.
- How do I apply for a personal loan?

## Security Notes

- Do not commit `.env`.
- Store `GEMINI_API_KEY` only in Render environment variables.
- If an API key is ever exposed, rotate it immediately.
- `chroma_db/` is ignored because it is generated locally during ingestion.

## Author

Built by Anurag Sharma as a banking-focused RAG chatbot project.
