# DocChat

A FastAPI-based “chat with your PDFs” application. PDFs are parsed with
PyMuPDF, embedded locally with BGE, stored in ChromaDB, and answered with
Gemini using hybrid semantic and keyword retrieval.

## Run locally

```powershell
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
uvicorn app.main:app --reload
```

Open `http://127.0.0.1:8000` in your browser.

## Features

- Responsive ChatGPT-style web interface
- Multi-PDF upload and drag-and-drop
- Persistent document library
- Select one or several PDFs as the chat scope
- Hybrid semantic and lexical retrieval
- Page-level source references
- Document deletion and local chat history

## API

- `GET /documents` — list indexed PDFs
- `POST /documents/upload` — upload and index a PDF
- `DELETE /documents/{document_id}` — remove a PDF and its vectors
- `POST /chat` — ask selected documents a question
- `GET /health` — application health check
