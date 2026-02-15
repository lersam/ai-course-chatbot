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
   ollama pull gemma3:4b
   ollama pull qwen3-embedding:4b
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

Load a PDF and start chatting:

```bash
python ai_course_chatbot/setup_vector_store.py --pdf path/to/your/document.pdf
```

### Multiple PDFs

Load multiple PDF files:

```bash
python ai_course_chatbot/setup_vector_store.py --pdf file1.pdf file2.pdf file3.pdf
```

### Custom Model

Use a different Ollama model (or set `OLLAMA_MODEL` environment variable). The project defaults to `gemma3:4b`.

```bash
python ai_course_chatbot/setup_vector_store.py --pdf document.pdf --model gemma3:4b
# or set environment variable: export OLLAMA_MODEL=gemma3:4b  (Windows: set OLLAMA_MODEL=gemma3:4b)
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

### Force Reload

Force reload PDFs even if vector store exists:

```bash
python main.py --pdf document.pdf --reload
```

### Available Options

- `--pdf`: Path(s) to PDF file(s) to load (required for first run)
- `--model`: Ollama LLM model to use (default: gemma3:4b). You can also set the `OLLAMA_MODEL` env var.
- `--embedding-model`: Ollama embedding model (default: qwen3-embedding:4b)
- `--reload`: Force reload PDFs into vector store

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
│  ┌──────────────────┐          ┌──────────────────┐             │
│  │  Query Handler   │◄────────►│   Ollama LLM     │             │
│  │  RetrievalQA     │          │   (gemma3:4b)       │             │
│  └─────────┬────────┘          └──────────────────┘             │
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
               (qwen3-embedding:4b)
```

Notes:
- The helper function `setup_vector_store(pdf_paths)` accepts explicit PDF paths and loads those PDFs into a newly-created `VectorStore`. It does not auto-detect or load an existing vector store on disk.
- If no PDFs are provided or no documents are extracted, the function will return None so ingestion remains deterministic.

### Components

- **PDF Loader (`pdf_loader.py`)**: loads and chunks PDFs (default chunk size 1000, overlap 200).
-- **Vector Store (`vector_store.py`)**: manages embeddings and stores them in ChromaDB (embedding model: `qwen3-embedding:4b`).
- **RAG Chatbot (`rag_chatbot.py`)**: handles queries, retrieval, and LLM generation using Ollama.
- **Chat Router (`chat_router.py`)**: FastAPI endpoints for web-based chat interface.
- **Web Interface (`static/`)**: HTML, CSS, and JavaScript for the chat UI.
- **Worker (`worker.py`)**: Celery tasks for background processing (SQLite SQLAlchemy transport/result backend).
- **Monitoring**: FastAPI endpoints `/monitoring/` and `/monitoring/celery-task` expose task info using an SQLite DB fallback when inspect returns empty.

## Project Structure

```
ai-course-chatbot/
├── ai_course_chatbot/   # Python package
│   ├── main.py          # Main application entry point (FastAPI)
│   ├── setup_vector_store.py
│   ├── worker.py
│   ├── ai_modules/      # pdf_loader, vector_store, rag_chatbot, etc.
│   ├── models/          # Pydantic models for requests/responses
│   ├── routers/         # FastAPI routers (chat, pdf, monitoring)
│   └── static/          # Frontend assets (HTML, CSS, JS)
│       ├── index.html   # Chat interface
│       ├── css/
│       └── js/
├── tests/               # Test suite
├── requirements.txt     # Python dependencies
├── README.md            # This file
└── chroma_db/           # Vector database storage (created automatically)
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

Initializing chatbot with model: gemma3:4b

============================================================
AI RAG Chatbot (Model: gemma3:4b)
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
- Use smaller models (e.g., `gemma3:4b`) when running on limited hardware

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