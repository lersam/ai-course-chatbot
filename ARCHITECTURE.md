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
│  │  RetrievalQA     │          │   (gemma3)       │             │
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
                                    (qwen3-embedding)
```

Notes:
- The helper function `setup_vector_store(pdf_paths)` now strictly accepts explicit PDF paths and loads those PDFs into a newly-created `VectorStore`. It does not attempt to auto-detect or load an existing vector store on disk.
- If no PDFs are provided or no documents are extracted, the function will return None (and the CLI will report the issue). This makes ingestion deterministic and explicit.

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
                       (gemma3)
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
- **Purpose**: Manage document embeddings and retrieval
- **Key Functions**:
  - `add_documents()`: Add documents to vector store
  - `load_existing()`: Load existing vector store (kept for backward compatibility but not used by `setup_vector_store`)
  - `similarity_search()`: Search for similar documents
  - `get_retriever()`: Get retriever for RAG
- **Storage**: ChromaDB (persistent on disk)
-- **Embeddings**: Ollama qwen3-embedding

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

### Main Application (`setup_vector_store.py`)
- **Purpose**: CLI entry point and helper to build a VectorStore from PDFs
- **Key Functions**:
  - `setup_vector_store(pdf_paths)`: Initialize a new VectorStore by loading the provided PDF paths. This helper requires explicit PDF paths and will return the populated `VectorStore` or None if no documents were loaded.
  - `main()`: Optional helper that parses CLI args and calls `setup_vector_store`.
- **Arguments**:
  - `--pdf`: PDF files to load (required to build a vector store)
  - `--model`: LLM model to use (default: gemma3)
  - `--embedding-model`: Embedding model (default: qwen3-embedding)

Notes:
- The previous `--reload`/auto-reload behavior was intentionally removed: re-loading or overwriting an existing collection must be handled explicitly by the user or by an enhanced helper if desired.

## External Dependencies

- **gemma3**: Language model for text generation
- **qwen3-embedding**: Embedding model for vector representations

### Python Libraries
- **langchain**: RAG framework
- **langchain-community**: Community integrations
- **chromadb**: Vector database
- **pypdf**: PDF processing
- **ollama**: Ollama client

## Configuration

### Environment Variables
- Not currently used, but can be added for:
  - Ollama API endpoint
  - Model names
  - Vector store path

### Default Settings
- Chunk size: 1000 characters
- Chunk overlap: 200 characters
- LLM model: gemma3
- Embedding model: qwen3-embedding
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
