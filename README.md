# AI Course Chatbot

A simple Retrieval-Augmented Generation (RAG) chatbot that loads PDF files, stores them in a vector database, and enables intelligent Q&A using Ollama.

## Features

- 📄 **PDF Loading**: Automatically loads and processes PDF documents
- 🔍 **Vector Storage**: Stores document embeddings in ChromaDB for efficient retrieval
- 🤖 **AI-Powered Q&A**: Uses Ollama LLMs for natural language responses
- 💬 **Interactive Chat**: Both web-based UI and command-line interface for asking questions
- 🌐 **Web Interface**: Modern, responsive chat interface with real-time messaging
- 📚 **Source Citations**: Shows source documents and page numbers
- 🔄 **RESTful API**: FastAPI endpoints for chat, PDF upload, and monitoring

## Prerequisites

Before running the application, ensure you have:

1. **Python 3.10+** installed
2. **Ollama** installed and running locally
   - Install from: https://ollama.ai
   - Pull required models:
   ```bash
   ollama pull gemma3:4b-it-qat
   ollama pull nomic-embed-text
   ```

## Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/lersam/ai-course-chatbot.git
   cd ai-course-chatbot
   ```

2. Create a virtual environment (recommended):
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## Usage

### Web Interface (Recommended)

1. Start the FastAPI server:
   ```bash
   uvicorn ai_course_chatbot.main:app --host 0.0.0.0 --port 8000 --reload
   ```

2. Open your browser and navigate to:
   ```
   http://localhost:8000
   ```

3. You'll see a modern chat interface where you can:
   - Ask questions about your uploaded documents
   - View source citations for answers
   - Toggle source display on/off
   - Get real-time responses

4. Upload PDFs using the API endpoints (see below) or use the existing CLI tools

### API Endpoints

The application provides several REST endpoints:

- **`GET /`** - Web chat interface
- **`POST /chat/`** - Send a chat message
  ```bash
  curl -X POST "http://localhost:8000/chat/" \
    -H "Content-Type: application/json" \
    -d '{"message": "What is this document about?", "show_sources": true}'
  ```
- **`GET /chat/status`** - Check chatbot status
- **`POST /pdf/download`** - Download and process a PDF from URL
- **`POST /pdf/upload`** - Upload a PDF file
- **`GET /monitoring/`** - View Celery task status

### Basic Usage (CLI)

Load a PDF and build (or rebuild) the Chroma vector store that the API uses:

```bash
python ai_course_chatbot/setup_vector_store.py --pdf path/to/your/document.pdf
```

> The CLI helper only ingests PDFs and prepares the database. Run the FastAPI server (see "Web Interface") to chat with the documents you just loaded.

### Multiple PDFs

Load multiple PDF files:

```bash
python ai_course_chatbot/setup_vector_store.py --pdf file1.pdf file2.pdf file3.pdf
```

### Custom Model

The FastAPI service instantiates `RAGChatbot` with `gemma3:4b-it-qat` by default. Override it by setting `OLLAMA_MODEL` before starting the server, or by passing the `--model` flag to the ingestion CLI (which sets `OLLAMA_MODEL` for downstream chat sessions):

```bash
export OLLAMA_MODEL=gemma3:2b-instruct  # choose any Ollama model you've pulled
uvicorn ai_course_chatbot.main:app --host 0.0.0.0 --port 8000 --reload
```

### HTTP API example: POST /pdf/download

Instead of using the CLI, you can call the FastAPI endpoint directly to download and queue a PDF for processing (this example posts a JSON body). The `topics` field accepts one of the Topics enum values (for example `GameProgrammingBooks`).

Curl example:

```bash
curl -X POST "http://localhost:8000/pdf/download" \
   -H "Content-Type: application/json" \
   -d '{"url": "https://inventwithpython.com/makinggames.pdf"}'
```

Python requests example:

```python
import requests

resp = requests.post(
      "http://localhost:8000/pdf/download",
      json={
            "url": "https://inventwithpython.com/makinggames.pdf",
            "topics": "GameProgrammingBooks"
      }
)
print(resp.json())
```

### Running Celery (SQLite only)

This project uses the SQLAlchemy/SQLite transport by default for both the broker
and the result backend. Ensure the system `sqlite3` CLI and the Python
packages in `requirements.txt` are installed (`kombu-sqlalchemy`, `SQLAlchemy`).

Start the Celery worker from the project root:

```bash
celery -A ai_course_chatbot.worker.celery worker --loglevel=info
```

If you change the broker/result backend via `CELERY_BROKER_URL` or
`CELERY_RESULT_BACKEND`, make sure they point to `sqla+sqlite:///...` or
`db+sqlite:///...` respectively so the code and status endpoint continue to
work with the SQLite fallback.

### Monitoring Celery tasks

This project exposes simple monitoring endpoints and a DB fallback for
observability when using the SQLite result backend.

-- `GET /monitoring/` — Returns all tasks discovered via the SQLite result
   backend (reads the `celery_taskmeta` table). Useful when Celery's
   remote-control `inspect` returns no results (SQL transport limitation).
-- `GET /monitoring/celery-task` — Returns only currently running tasks (statuses
   like `RUNNING`, `STARTED`, or `ACTIVE`) as `CeleryTaskStatus` models.

Example curl calls:

```bash
curl http://localhost:8000/monitoring/
curl http://localhost:8000/monitoring/celery-task?celery_task=<task_id>
```

Inspect the SQLite result DB directly (useful for debugging):

```bash
# print configured result backend
python -c "from ai_course_chatbot.worker import celery; print(celery.conf.result_backend)"

# open DB (example path: ./celery_results.sqlite)
sqlite3 ./celery_results.sqlite
.tables
SELECT task_id, status, date_done, traceback FROM celery_taskmeta ORDER BY date_done DESC;
.exit
```

Notes:
- The `update_vector_store` task sets its Celery state to `RUNNING` at start
   (best-effort). The status endpoints and DB will reflect that while the
   task is executing.
- Ensure the system `sqlite3` binary and Python packages `kombu-sqlalchemy`
   and `SQLAlchemy` are installed so the SQL transport and result backend
   function correctly.

### Rebuild the Vector Store

By default, `setup_vector_store.py` **appends** new documents to the existing Chroma collection with automatic deduplication. This allows you to incrementally add documents without losing existing data:

```bash
python ai_course_chatbot/setup_vector_store.py --pdf new_document.pdf
```

To **completely rebuild** the collection (clearing all existing documents first), use the `--rebuild` flag:

```bash
python ai_course_chatbot/setup_vector_store.py --pdf document.pdf --rebuild
```

Use `--rebuild` when you need to start fresh, such as when changing embedding models or fixing corrupted data.

### Available Options

- `--pdf`: Path(s) to PDF file(s) to load (required)
- `--rebuild`: Clear the existing collection before loading documents (optional; default is to append with deduplication)
- `--model`, `--embedding-model`: Runtime chat behavior is controlled via the `OLLAMA_MODEL` environment variable.

## How It Works

1. **PDF Loading**: The application uses PyPDF to extract text from PDF documents
2. **Text Chunking**: Documents are split into manageable chunks with overlap for context
3. **Embedding Generation**: Text chunks are converted to embeddings using Ollama's embedding model
4. **Vector Storage**: Embeddings are stored in ChromaDB for efficient similarity search
5. **Query Processing**: User questions are embedded and matched against stored documents
6. **Answer Generation**: Relevant context is retrieved and passed to the LLM for answer generation

## Architecture

### System Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                        User Interface                           │
│                  (setup_vector_store.py)                        │
│                    Command Line Interface                       │
└───────────────────────────┬─────────────────────────────────────┘
            │
            ▼
┌─────────────────────────────────────────────────────────────────┐
│                      RAG Chatbot Layer                          │
│                      (rag_chatbot.py)                           │
│  ┌──────────────────┐          ┌────────────────────────┐       │
│  │  Query Handler   │◄────────►│   Ollama LLM           │       │
│  │  RetrievalQA     │          │   (gemma3:4b-it-qat)   │       │
│  └─────────┬────────┘          └────────────────────────┘       │
└────────────┼────────────────────────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────────────────────────────────┐
│                    Vector Store Layer                           │
│                    (vector_store.py)                            │
│  ┌────────────────────────────────────────────────────┐         │
│  │             ChromaDB Vector Database               │         │
│  │  ┌──────────────┐        ┌──────────────────┐      │         │
│  │  │  Embeddings  │◄──────►│ Similarity Search│      │         │
│  │  │   Storage    │        │    & Retrieval   │      │         │
│  │  └──────────────┘        └──────────────────┘      │         │
│  └────────────────────────────────────────────────────┘         │
└────────────┬────────────────────────────────────────────────────┘
         │
         ▼
┌────────────────────────────────────────────────────────────────┐
│                  Document Processing Layer                     │
│                     (pdf_loader.py)                            │
│  ┌──────────────┐         ┌──────────────────┐                 │
│  │  PDF Loader  │────────►│  Text Splitter   │                 │
│  │  (PyPDF)     │         │  (Chunking)      │                 │
│  └──────────────┘         └──────────────────┘                 │
└────────────┬───────────────────────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────────────────────────────────┐
│                         Data Source                             │
│                       PDF Documents                             │
└─────────────────────────────────────────────────────────────────┘
```

### Data Flow

```
PDF Files → PDF Loader → Text Chunks → Embeddings → Vector Store
                   ▲
                   │
                Ollama Embeddings
               (nomic-embed-text)
```

Notes:
- The helper function `setup_vector_store(pdf_paths)` accepts explicit PDF paths and loads those PDFs into a newly-created `VectorStore`. It does not auto-detect or load an existing vector store on disk.
- If no PDFs are provided or no documents are extracted, the function will return None so ingestion remains deterministic.

### Components

- **PDF Loader (`ai_modules/pdf_loader.py`)**: extracts and chunks PDF text (chunk size 1000, overlap 200) for downstream embeddings.
- **Vector Store (`ai_modules/vector_store.py`)**: wraps ChromaDB plus `nomic-embed-text` embeddings, handling add/load/search operations.
- **RAG Chatbot (`ai_modules/rag_chatbot.py`)**: wires the retriever into LangChain's `RetrievalQA` and proxies to the Ollama chat model (default `gemma3:4b-it-qat`).
- **Routers (`routers/`)**: `chat_router.py` serves chat/status, `pdf_router.py` schedules ingestion jobs, and `monitoring.py` exposes Celery task visibility.
- **Controllers (`controllers/`)**: shared helpers to download/upload PDFs and to inspect Celery's SQLite result backend.
- **Worker (`worker.py`)**: Celery task `update_vector_store` that rebuilds the Chroma collection asynchronously when PDF uploads/downloads finish.
- **Web Interface (`static/`)**: HTML, CSS, and JavaScript assets served by FastAPI to provide the chat UI.

## Project Structure

```
ai-course-chatbot/
├── ai_course_chatbot/           # Application package
│   ├── ai_modules/              # pdf_loader, vector_store, rag_chatbot
│   ├── controllers/             # download helpers + Celery status helpers
│   ├── models/                  # Pydantic request/response objects
│   ├── routers/                 # chat, pdf, and monitoring FastAPI routers
│   ├── static/                  # Frontend assets (index.html, css, js)
│   ├── main.py                  # FastAPI entry point
│   ├── setup_vector_store.py    # CLI helper to ingest PDFs
│   └── worker.py                # Celery tasks
├── data/
│   └── examples_to_run.txt      # Sample prompts and document references
├── tests/                       # Pytest suite exercising loaders/routers
├── example.py                   # Minimal script demonstrating programmatic use
├── ARCHITECTURE.md              # Detailed architecture notes
├── QUICKSTART.md                # Condensed setup guide
├── requirements.txt             # Python dependencies
├── README.md                    # This document
└── chroma_db/                   # Generated ChromaDB persistence directory
```

## Example Interaction

### Web Interface

After starting the server and navigating to `http://localhost:8000`, you'll see a modern chat interface:

![AI Course Chatbot Interface](https://github.com/user-attachments/assets/c12a7dcc-d79d-448b-9bfa-b180854a395f)

The interface features:
- **Real-time chat**: Send messages and receive instant responses
- **Source citations**: Toggle to show/hide document sources
- **Status indicator**: Shows when the chatbot is ready
- **Responsive design**: Works on desktop and mobile devices
- **Chat history**: Scroll through previous messages

![Chat Conversation Example](https://github.com/user-attachments/assets/18f65661-3286-42ff-9d21-7a634005a673)

### CLI Interface

```
============================================================
AI RAG Chatbot - PDF Document Q&A
============================================================
Loading PDF files...
Loaded 50 pages from document.pdf
Split into 125 chunks

Creating vector store...
Added 125 documents to vector store
Vector store created successfully!

Initializing chatbot with model: gemma3:4b-it-qat

============================================================
AI RAG Chatbot (Model: gemma3:4b-it-qat)
============================================================
Type 'quit' or 'exit' to end the conversation.

You: What is the main topic of this document?

Chatbot: Based on the provided context, the main topic of this document is...

Sources:
1. document.pdf (Page 1)
2. document.pdf (Page 2)

You: exit
Goodbye!
```

## Troubleshooting

### Ollama Connection Issues
- Ensure Ollama is running: `ollama serve`
- Check if models are installed: `ollama list`

### Memory Issues
- Reduce chunk size in `pdf_loader.py` if processing large PDFs
- Use smaller models (e.g., `gemma3:4b-it-qat`) when running on limited hardware

### Import Errors
- Reinstall dependencies: `pip install -r requirements.txt --upgrade`

### Celery: Unregistered task

If you see an error like "Received unregistered task" for `ai_course_chatbot.worker.update_vector_store`, try the following:

- **Check worker startup**: start the worker with the same app path used in the project:

```bash
celery -A ai_course_chatbot.worker.celery worker --loglevel=info
```

- **Inspect registered tasks** (run while the worker is running):

```bash
celery -A ai_course_chatbot.worker.celery inspect registered
```

- **Confirm module import**: ensure the worker module is imported by the Celery app. The project already sets `celery.conf.imports = ['ai_course_chatbot.worker']` in `ai_course_chatbot/worker.py`, but if you're structuring tasks elsewhere, add the module to `imports` or use `include=` when creating the `Celery` instance.

- **Check PYTHONPATH / working directory**: run the worker from the repository root and ensure your virtualenv is active so `ai_course_chatbot` is importable.

- **Quick Python check**: run this to confirm the task is discoverable by import (no worker required):

```bash
python -c "import ai_course_chatbot.worker as w; print([k for k in w.celery.tasks.keys() if 'update_vector_store' in k])"
```

-- **Broker / backend**: this project defaults to SQLite. If you changed the
backend, ensure `CELERY_BROKER_URL` and `CELERY_RESULT_BACKEND` remain set to
SQLite URLs (for example `sqla+sqlite:///./celerydb.sqlite` and
`db+sqlite:///./celery_results.sqlite`). Note: the SQL transport may not
support control broadcasts reliably, which can make `inspect` return empty —
the `/monitoring/` endpoint has a SQLite fallback that reads `celery_taskmeta`.

If the issue persists, consider moving tasks to a dedicated `tasks.py` module
and using `@shared_task` or adjusting `celery.conf.imports` to include the
module path.

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.