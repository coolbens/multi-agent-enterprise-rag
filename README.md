# Multi-Agent Enterprise RAG System

An AI application for uploading company documents and asking source-grounded questions using **React**, **FastAPI**, **LangGraph**, **LangChain**, **OpenAI**, **Hugging Face embeddings**, **ChromaDB**, **SQLite**, and **Docker**.

This project demonstrates a realistic enterprise GenAI architecture:

- Multi-document ingestion: PDF, DOCX, TXT, CSV, XLSX
- Retrieval-Augmented Generation with citations
- LangGraph multi-agent workflow
- JWT authentication and admin dashboard
- SQL database for users, documents, and deletable chat memory
- Vector database for embeddings and semantic search
- React frontend with modern dashboard UI and conversation history controls
- Docker-ready deployment structure

## Architecture

```text
React Frontend
   ↓
FastAPI Backend + JWT Auth
   ↓
SQLAlchemy + SQLite
   ↓
Document Loader → Chunking → Hugging Face Embeddings
   ↓
ChromaDB / Qdrant / Pinecone
   ↓
LangGraph Workflow
Retrieve → Analyze → Summarize → Verify → Final Answer
   ↓
OpenAI LLM + Citations
```

## Tech Stack

### Frontend
- React
- Vite
- CSS
- Lucide React icons

### Backend
- Python 3.11
- FastAPI
- SQLAlchemy
- Pydantic
- JWT authentication
- Passlib password hashing

### AI / RAG
- OpenAI chat model
- LangChain
- LangGraph
- Hugging Face embeddings
- ChromaDB default vector database
- Optional Pinecone and Qdrant support

## Project Structure

```text
multi_agent_enterprise_rag/
├── backend/
│   ├── app/
│   │   ├── agents/rag_graph.py
│   │   ├── routes/
│   │   ├── services/
│   │   ├── models/
│   │   ├── schemas/
│   │   └── core/
│   ├── requirements.txt
│   └── .env.example
├── frontend/
│   ├── src/
│   ├── package.json
│   ├── vite.config.js
│   └── Dockerfile
├── sample_docs/
├── docs/
├── scripts/
└── docker-compose.yml
```

## Local Setup

### 1. Create and activate virtual environment

```powershell
cd C:\Users\BCarnoco\Documents\multi_agent_enterprise_rag
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

If PowerShell blocks activation:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\.venv\Scripts\Activate.ps1
```

### 2. Install backend dependencies

```powershell
cd backend
pip install -r requirements.txt
```

### 3. Create backend environment file

Copy:

```text
backend/.env.example
```

Rename the copy to:

```text
backend/.env
```

Add your OpenAI API key:

```env
OPENAI_API_KEY=sk-your-key-here
```

### 4. Run backend

```powershell
cd backend
uvicorn app.main:app --reload
```

Open:

```text
http://127.0.0.1:8000/docs
```

Default admin account:

```text
Email: admin@example.com
Password: admin123
```

Change this before deployment.

### 5. Run React frontend

Open a new terminal:

```powershell
cd frontend
npm install
npm run dev
```

Open:

```text
http://localhost:5173
```

## Docker Setup

For Docker, first edit `backend/.env.example` and add your OpenAI API key or create `backend/.env` and update `docker-compose.yml` to use it.

```powershell
docker compose up --build
```

Frontend:

```text
http://localhost:5173
```

Backend API:

```text
http://localhost:8000/docs
```

## How to Use

1. Login as admin or register a user.
2. Upload sample company documents from `sample_docs/`.
3. Ask questions in the AI Chat page.
4. Review the agent workflow and citations.
5. Check chat memory in History.
6. Use Admin page to view system counts and vector stats.

## Sample Questions

```text
What is the company password policy?
What are the remote work rules?
What does the IT manual say about support requests?
Summarize the employee data security policy.
```

## Important Folders Created Automatically

```text
backend/storage/app.db      SQL database
backend/uploads/            Uploaded files
backend/chroma_db/          Local vector database
```

## Common Debug Fixes

### SQLite unable to open database file

The app now uses absolute paths and auto-creates folders. If it still happens, delete and recreate:

```powershell
cd backend
mkdir storage
```

### Chroma settings conflict

Stop backend, then reset Chroma:

```powershell
cd backend
Remove-Item -Recurse -Force chroma_db
mkdir chroma_db
```

Upload your documents again after reset.

### Missing OpenAI key

Create `backend/.env` and add:

```env
OPENAI_API_KEY=sk-your-key-here
```

### Hugging Face model download is slow

The first upload may take longer because `sentence-transformers/all-MiniLM-L6-v2` downloads once.

## API Endpoints

- `POST /auth/register`
- `POST /auth/login`
- `POST /documents/upload`
- `GET /documents/list`
- `DELETE /documents/delete/{id}`
- `POST /chat/ask`
- `GET /chat/history`
- `GET /admin/dashboard`
- `GET /health`



## Recent polish checks

This version includes:

- React conversation-memory delete buttons
- Backend user-scoped delete endpoints for chat history
- Safe JSON parsing for saved chat history
- Absolute backend paths for SQLite, uploads, and ChromaDB
- Auto-created runtime folders: `backend/storage`, `backend/uploads`, `backend/chroma_db`
- Cache files removed from the ZIP

## Chat memory API

```text
GET    /chat/history
DELETE /chat/history/{message_id}
DELETE /chat/history
```

Deletion is scoped to the authenticated user. A user cannot delete another user's conversation memory.
