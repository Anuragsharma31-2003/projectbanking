# Banking RAG Chatbot

FastAPI + Streamlit chatbot for banking document Q&A. The backend ingests PDF/TXT/MD files into ChromaDB, retrieves relevant chunks with Sentence Transformers, reranks them, and generates answers with Gemini.

## Local Setup

Use Python 3.11 on Windows.

```powershell
py -3.11 -m venv venv
.\venv\Scripts\Activate.ps1
python -m pip install --upgrade pip setuptools wheel
python -m pip install -r backend\requirements.txt
```

Create `.env` from `.env.example` and add your Gemini API key:

```env
GEMINI_API_KEY=your_gemini_api_key_here
GEMINI_MODEL=gemini-2.5-flash
```

Ingest the documents:

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

## Deployment Notes

Do not commit `.env`, `venv/`, `venv-py312/`, or `chroma_db/`. Configure `GEMINI_API_KEY` as an environment variable on your hosting provider.
