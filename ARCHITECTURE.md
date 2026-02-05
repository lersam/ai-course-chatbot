# System Architecture

## Overview

The AI Course Chatbot uses a RAG (Retrieval-Augmented Generation) architecture to answer questions about PDF documents using local LLMs via Ollama.

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                          User Interface                          │
│                         (CLI - main.py)                          │
└──────────────────────────┬──────────────────────────────────────┘
                           │
                           ▼
         ┌─────────────────────────────────────┐
         │      1. Load PDFs                   │
         │   (PDFLoader)                       │
         │   - Extract text page by page       │
         │   - Create document objects         │
         └──────────────┬──────────────────────┘
                        │
                        ▼
         ┌─────────────────────────────────────┐
         │   2. Generate Embeddings            │
         │   (VectorStore + Ollama)            │
         │   - Use nomic-embed-text model      │
         │   - Convert text to vectors         │
         └──────────────┬──────────────────────┘
                        │
                        ▼
         ┌─────────────────────────────────────┐
         │   3. Store in Vector DB             │
         │   (ChromaDB)                        │
         │   - Persist embeddings              │
         │   - Enable similarity search        │
         └──────────────┬──────────────────────┘
                        │
                        ▼
         ┌─────────────────────────────────────┐
         │   4. User Query                     │
         │   - Convert query to embedding      │
         │   - Search similar documents        │
         └──────────────┬──────────────────────┘
                        │
                        ▼
         ┌─────────────────────────────────────┐
         │   5. Retrieve Context               │
         │   (VectorStore.query)               │
         │   - Top-k most similar chunks       │
         │   - Include metadata (source, page) │
         └──────────────┬──────────────────────┘
                        │
                        ▼
         ┌─────────────────────────────────────┐
         │   6. Generate Answer                │
         │   (RAGChatbot + Ollama)             │
         │   - Format prompt with context      │
         │   - Generate response with LLM      │
         │   - Return answer with sources      │
         └─────────────────────────────────────┘
```

## Component Details

### 1. PDF Loader (`src/pdf_loader.py`)

**Responsibility:** Extract text from PDF files

**Key Methods:**
- `load()` - Reads PDF and extracts text page by page
- Returns list of documents with content and metadata

**Technologies:** pypdf

### 2. Vector Store (`src/vector_store.py`)

**Responsibility:** Manage embeddings and similarity search

**Key Methods:**
- `__init__()` - Initialize ChromaDB client and collection
- `_generate_embedding()` - Create embeddings using Ollama
- `add_documents()` - Store document embeddings
- `query()` - Search for similar documents
- `clear()` - Reset the vector store

**Technologies:** ChromaDB, Ollama

### 3. RAG Chatbot (`src/chatbot.py`)

**Responsibility:** Orchestrate retrieval and generation

**Key Methods:**
- `chat()` - Main chat function
  1. Retrieve relevant documents
  2. Format context
  3. Generate prompt
  4. Call LLM for response
- `_format_context()` - Structure retrieved documents

**Technologies:** Ollama

### 4. Main Application (`main.py`)

**Responsibility:** CLI interface and workflow orchestration

**Key Functions:**
- `load_pdfs()` - Batch PDF loading
- `chat_loop()` - Interactive chat interface
- `main()` - Entry point with argument parsing

**Technologies:** argparse

## Data Flow

### Indexing Phase (Loading PDFs)

```
PDF File → PDFLoader → Text Chunks → Ollama (Embeddings) → ChromaDB
```

### Query Phase (Asking Questions)

```
User Question → Ollama (Embedding) → ChromaDB (Search) → Retrieved Context
              ↓
User Question + Context → Ollama (LLM) → Answer
```

## Technology Stack

| Component | Technology | Purpose |
|-----------|------------|---------|
| PDF Processing | pypdf | Extract text from PDFs |
| Vector Database | ChromaDB | Store and search embeddings |
| LLM Inference | Ollama | Local model inference |
| Embeddings | nomic-embed-text | Convert text to vectors |
| Chat Model | llama2/mistral | Generate responses |
| CLI | argparse | Command-line interface |

## Key Design Decisions

### 1. Local LLM (Ollama)
- **Why:** Privacy, no API costs, offline capability
- **Trade-off:** Requires local resources

### 2. ChromaDB
- **Why:** Simple, persistent, good for prototypes
- **Alternative:** Could use FAISS, Pinecone, etc.

### 3. Page-level Chunking
- **Why:** Simple implementation, preserves page context
- **Improvement:** Could implement semantic chunking

### 4. Synchronous Processing
- **Why:** Simpler code, easier to debug
- **Improvement:** Could add async for better performance

## Scalability Considerations

### Current Limitations
- Synchronous processing (one PDF at a time)
- In-memory document processing
- Page-level chunking (may be too large)

### Future Improvements
1. **Async Processing:** Use asyncio for parallel PDF loading
2. **Chunking Strategy:** Implement sliding window or semantic chunking
3. **Caching:** Cache embeddings to avoid recomputation
4. **Streaming:** Stream responses for better UX
5. **Multi-modal:** Support images and tables from PDFs

## Security Considerations

### Current Implementation
- Local processing (no data sent to external services)
- No authentication (local use only)
- File system access (reads from specified directories)

### Production Recommendations
1. Add input validation for file paths
2. Implement rate limiting for API-like usage
3. Add user authentication if multi-user
4. Sanitize PDF content before processing
5. Add resource limits (file size, memory)

## Performance Characteristics

### Indexing (Loading PDFs)
- **Time:** ~1-5 seconds per page (depends on model)
- **Memory:** Depends on PDF size and model
- **Disk:** ChromaDB stores embeddings persistently

### Querying
- **Time:** ~1-3 seconds per query
  - Embedding generation: ~0.5s
  - Vector search: <0.1s
  - LLM generation: 1-3s
- **Memory:** Depends on context size and model

## Extension Points

1. **Custom Embedding Models:** Change `embedding_model` parameter
2. **Custom Chat Models:** Change `model` parameter
3. **Custom Prompts:** Modify `RAGChatbot.chat()` method
4. **Additional File Types:** Add loaders in `src/` directory
5. **Web Interface:** Replace CLI with Gradio/Streamlit
6. **API Server:** Wrap in FastAPI/Flask

