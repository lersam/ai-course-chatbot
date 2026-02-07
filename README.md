# AI Course Chatbot

A simple Retrieval-Augmented Generation (RAG) chatbot that loads PDF files, stores them in a vector database, and enables intelligent Q&A using Ollama.

## Features

- 📄 **PDF Loading**: Automatically loads and processes PDF documents
- 🔍 **Vector Storage**: Stores document embeddings in ChromaDB for efficient retrieval
- 🤖 **AI-Powered Q&A**: Uses Ollama LLMs for natural language responses
- 💬 **Interactive Chat**: Command-line interface for asking questions
- 📚 **Source Citations**: Shows source documents and page numbers

## Prerequisites

Before running the application, ensure you have:

1. **Python 3.8+** installed
2. **Ollama** installed and running locally
   - Install from: https://ollama.ai
   - Pull required models:
     ```bash
     ollama pull llama2
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

### Basic Usage

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

Use a different Ollama model:

```bash
python ai_course_chatbot/setup_vector_store.py --pdf document.pdf --model mistral
```

### HTTP API example: POST /pdf/load

Instead of using the CLI, you can call the FastAPI endpoint directly to load a PDF (this example posts a JSON body). The `topics` field accepts one of the Topics enum values (for example `GameProgrammingBooks`).

Curl example:

```bash
curl -X POST "http://localhost:8000/pdf/load" \
  -H "Content-Type: application/json" \
  -d '{"url": "https://inventwithpython.com/makinggames.pdf", "topics": "GameProgrammingBooks"}'
```

Python requests example:

```python
import requests

resp = requests.post(
    "http://localhost:8000/pdf/load",
    json={
        "url": "https://inventwithpython.com/makinggames.pdf",
        "topics": "GameProgrammingBooks"
    }
)
print(resp.json())
```

### Running Celery

Run a Celery worker for background tasks (ensure a message broker like Redis or RabbitMQ is running):

```bash
celery -A ai_course_chatbot.worker.celery worker --loglevel=info
```

If using Redis as the broker, start it first (example):

```bash
redis-server
```

### Force Reload

Force reload PDFs even if vector store exists:

```bash
python main.py --pdf document.pdf --reload
```

### Available Options

- `--pdf`: Path(s) to PDF file(s) to load (required for first run)
- `--model`: Ollama LLM model to use (default: llama2)
- `--embedding-model`: Ollama embedding model (default: nomic-embed-text)
- `--reload`: Force reload PDFs into vector store

## How It Works

1. **PDF Loading**: The application uses PyPDF to extract text from PDF documents
2. **Text Chunking**: Documents are split into manageable chunks with overlap for context
3. **Embedding Generation**: Text chunks are converted to embeddings using Ollama's embedding model
4. **Vector Storage**: Embeddings are stored in ChromaDB for efficient similarity search
5. **Query Processing**: User questions are embedded and matched against stored documents
6. **Answer Generation**: Relevant context is retrieved and passed to the LLM for answer generation

## Project Structure

```
ai-course-chatbot/
├── main.py              # Main application entry point
├── pdf_loader.py        # PDF loading and text chunking
├── vector_store.py      # Vector database management
├── rag_chatbot.py       # RAG chatbot implementation
├── requirements.txt     # Python dependencies
├── README.md           # This file
└── chroma_db/          # Vector database storage (created automatically)
```

## Example Interaction

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

Initializing chatbot with model: llama2

============================================================
AI RAG Chatbot (Model: llama2)
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
- Use smaller models (e.g., `llama2:7b` instead of `llama2:70b`)

### Import Errors
- Reinstall dependencies: `pip install -r requirements.txt --upgrade`

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.