# AI RAG Chatbot Architecture

## System Overview

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
│  │  RetrievalQA     │          │   (gemma3:4b)    │             │
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

## Data Flow

### 1. Document Ingestion
```
PDF Files → PDF Loader → Text Chunks → Embeddings → Vector Store
                                           ▲
                                           │
                                    Ollama Embeddings
                                    (qwen3-embedding:4b)
```

Notes:
- The helper function `setup_vector_store(pdf_paths)` strictly accepts explicit PDF paths and ingests them into the existing persisted collection; it does not auto-discover PDFs but relies on append/dedup behavior in the underlying vector store.
- Each chunk receives a deterministic ID derived from `source`, `page`, and a SHA-256 hash of its text. This allows fast duplicate filtering before issuing writes.
- If no PDFs are provided or no documents are extracted, the function returns `None` (and the CLI reports the issue). This keeps ingestion deterministic and explicit.

### 2. Query Processing
```
User Query → RAG Chatbot → Vector Store (Similarity Search)
                │                    │
                │                    ▼
                │              Relevant Chunks
                │                    │
                └───────────┬────────┘
                            ▼
                     Context + Query
                            │
                            ▼
                      Ollama LLM
                       (gemma3:4b)
                            │
                            ▼
                   Generated Answer + Sources
                            │
                            ▼
                          User
```

## Component Details

### PDF Loader (`pdf_loader.py`)
- **Purpose**: Load and process PDF documents
- **Key Functions**:
  - `load_pdf()`: Load single PDF
  - `load_multiple_pdfs()`: Load multiple PDFs
- **Parameters**:
  - `chunk_size`: 1000 characters (default)
  - `chunk_overlap`: 200 characters (default)

### Vector Store (`vector_store.py`)
- **Purpose**: Manage document embeddings, enforce deduplication, and surface retrievers
- **Key Functions**:
  - `add_documents()`: Normalizes metadata, generates deterministic IDs, filters existing hashes, and batches inserts
  - `clear_collection()`: Clears all documents from the collection and recreates it empty
  - `similarity_search()`: Search for similar documents
  - `get_retriever()`: Get retriever for RAG
- **Storage**: ChromaDB (persistent on disk with per-batch persistence helper)
- **Embeddings**: Ollama qwen3-embedding:4b

### RAG Chatbot (`rag_chatbot.py`)
- **Purpose**: Handle user queries with RAG
- **Key Functions**:
  - `ask()`: Answer single question
  - `chat()`: Interactive chat loop
- **Components**:
  - Ollama LLM for generation
  - RetrievalQA chain from LangChain
  - Custom prompt template
- **Features**:
  - Source citation with page numbers
  - Context-aware responses

### FastAPI Application (`main.py`)
- **Purpose**: Host the REST API, serve the SPA frontend, and warm up the chatbot on startup.
- **Responsibilities**:
  - Registers the `chat`, `pdf`, and `monitoring` routers.
  - Mounts `static/` (HTML/CSS/JS) under `/static` and serves `index.html` at `/`.
  - Calls `chat_router.get_chatbot()` during lifespan startup to instantiate a fresh `VectorStore`/`RAGChatbot` pair (ingestion must already have populated `./chroma_db`).

### Routers (`routers/`)
- **`chat_router.py`**
  - Instantiates a new `VectorStore` pointing at `./chroma_db` when the first chat/status call arrives; it assumes ingestion already built the on-disk collection and no longer tries to `load_existing()` explicitly.
  - Exposes `POST /chat/` and `GET /chat/status` (status reports `ready` once the chatbot instance exists, `not_ready` if initialization raised an HTTP error).
- **`pdf_router.py`**
  - Accepts `POST /pdf/download` (URL ingestion) and `POST /pdf/upload` (multipart uploads).
  - Uses controller helpers to save files to the temp downloads directory and schedules `worker.update_vector_store` via Celery.
- **`monitoring.py`**
  - Surfaces `/monitoring/` and `/monitoring/celery-task` which read task info from the SQLite `celery_taskmeta` table via controller helpers.
  - Relies on shared Pydantic models under `models/` such as `CeleryTaskStatus`.

### Controllers (`controllers/`)
- **`pdf_controller.py`**: Async-friendly utilities to download PDFs or persist uploaded bytes to the system temp directory (`tempfile.gettempdir()/ai-course-chatbot/downloads`).
- **`upload_status_controller.py`**: Functions that inspect the configured Celery SQLite backend (`celery_taskmeta`) using `aiosqlite` and return summarized status dictionaries.

### Worker (`worker.py`)
- **Purpose**: Defines the Celery app and the `update_vector_store` task.
- **Details**:
  - Defaults to SQLite for both broker (`sqla+sqlite:///./celerydb.sqlite`) and backend (`db+sqlite:///./celery_results.sqlite`).
  - `update_vector_store` calls `setup_vector_store(pdf_paths)` and manually updates task state to `RUNNING`/`SUCCESS`/`FAILURE` for the monitoring endpoints.

### Vector Store Builder (`setup_vector_store.py`)
- **Purpose**: CLI entry point that manages the Chroma collection by appending documents or rebuilding from an explicit list of PDF paths.
- **Key Functions**:
  - `setup_vector_store(pdf_paths, rebuild=False)`: Loads and chunks PDFs, then writes them into a `VectorStore` instance. By default, appends to existing collection with deduplication. When `rebuild=True`, clears the collection first. Returns the populated store or `None` if nothing was ingested.
  - `main()`: Parses CLI arguments and invokes `setup_vector_store` when `--pdf` values are provided.
- **Arguments**:
  - `--pdf`: One or more PDF files (required). The helper raises if no PDFs are supplied.
  - `--model`: Overrides the default chat model by setting the `OLLAMA_MODEL` environment variable before building the `VectorStore`.
  - `--embedding-model`: Embedding model name passed into `VectorStore` to control which embedding model is used for ingestion.
  - `--rebuild`: Clear the existing collection before loading documents (optional; default is to append with deduplication).

## External Dependencies

- **gemma3:4b**: Language model for text generation
- **qwen3-embedding:4b**: Embedding model for vector representations

### Python Libraries
- **langchain / langchain-community**: Retrieval orchestration and integrations
- **chromadb**: Persistent vector database
- **pypdf**: PDF text extraction
- **ollama / langchain-ollama**: Local LLM client
- **fastapi / starlette / uvicorn**: HTTP API and web server
- **celery / kombu-sqlalchemy / aiosqlite**: Background ingestion tasks and SQLite-backed status tracking

## Configuration

### Environment Variables
- `OLLAMA_MODEL` — overrides the default `gemma3:4b` that `chat_router` uses when instantiating `RAGChatbot`.
- `CELERY_BROKER_URL` / `CELERY_RESULT_BACKEND` — allow pointing the worker at a non-SQLite broker or backend (default to local SQLite files).
- `LANGCHAIN_TELEMETRY` / `ANONYMIZED_TELEMETRY` — set to `false` by `vector_store.py` to keep ingestion offline.

### Default Settings
- Chunk size: 1000 characters
- Chunk overlap: 200 characters
- LLM model: gemma3:4b (override via `OLLAMA_MODEL`)
- Embedding model: qwen3-embedding:4b
- Temperature: 0.7
- Retrieval k: 4 documents
- Vector store: ./chroma_db

## Scalability Considerations

### Current Implementation
- Single machine deployment
- Local Ollama instance
- Persistent ChromaDB storage
- Suitable for: Personal use, small teams, up to thousands of pages

### Potential Improvements
- Cloud-based vector store (Pinecone, Weaviate)
- Remote Ollama or OpenAI API
- Batch processing for large document sets
- Web interface (Streamlit, Gradio)
- Multi-user support with separate collections

## Security Features

### Implemented
- ✅ Updated dependencies (no known vulnerabilities)
- ✅ Local processing (no data sent to external APIs)
- ✅ Input validation and error handling
- ✅ No hardcoded credentials

### Best Practices
- Run in virtual environment
- Keep dependencies updated
- Sanitize file paths
- Validate PDF files before processing
- Use .env for sensitive configuration
