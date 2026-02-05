# AI Course Chatbot

A simple AI RAG (Retrieval-Augmented Generation) chatbot that loads PDF files and saves embeddings to a vector store using Ollama for local LLM inference.

## Features

- 📄 **PDF Loading**: Extract text from PDF files and process them
- 🔍 **Vector Store**: Store document embeddings using ChromaDB
- 🤖 **Local LLM**: Use Ollama for embeddings and chat completions
- 💬 **Interactive Chat**: Ask questions about your documents
- 🎯 **RAG Architecture**: Retrieve relevant context before generating answers

## Prerequisites

- Python 3.8 or higher
- [Ollama](https://ollama.ai/) installed and running
- Required Ollama models:
  - `llama2` (or any other chat model)
  - `nomic-embed-text` (for embeddings)

### Installing Ollama Models

```bash
# Pull the chat model
ollama pull llama2

# Pull the embedding model
ollama pull nomic-embed-text
```

## Installation

1. Clone the repository:
```bash
git clone https://github.com/lersam/ai-course-chatbot.git
cd ai-course-chatbot
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

## Usage

### Basic Usage

1. Place your PDF files in the `data` directory:
```bash
mkdir -p data
cp your-document.pdf data/
```

2. Run the chatbot:
```bash
python main.py
```

### Command Line Options

```bash
# Load specific PDF files
python main.py --pdfs path/to/document1.pdf path/to/document2.pdf

# Use a different Ollama model
python main.py --model mistral

# Use a different embedding model
python main.py --embedding-model mxbai-embed-large

# Clear existing vector store before loading new documents
python main.py --clear

# Specify a custom data directory
python main.py --data-dir /path/to/pdfs
```

### Example Session

```
$ python main.py --pdfs sample.pdf

Initializing vector store...
Loading PDF files...
Processing: sample.pdf
  Extracted 5 pages
  Added to vector store
All PDFs loaded successfully!

Initializing chatbot...
============================================================
AI Course Chatbot - Interactive Mode
============================================================
Ask questions about your documents. Type 'quit' or 'exit' to stop.

You: What is this document about?

Thinking...

Bot: Based on the provided context, this document appears to be about...

Sources:
  - sample.pdf, Page 1

You: quit
Goodbye!
```

## Project Structure

```
ai-course-chatbot/
├── src/
│   ├── __init__.py
│   ├── pdf_loader.py      # PDF loading functionality
│   ├── vector_store.py    # ChromaDB vector store management
│   └── chatbot.py         # RAG chatbot logic
├── data/                  # Directory for PDF files
├── chroma_db/            # ChromaDB persistence (auto-created)
├── main.py               # Main application entry point
├── requirements.txt      # Python dependencies
└── README.md            # This file
```

## How It Works

1. **PDF Loading**: The `PDFLoader` class extracts text from PDF files page by page.

2. **Embeddings**: Text from each page is converted into vector embeddings using Ollama's embedding model (`nomic-embed-text` by default).

3. **Vector Store**: Embeddings are stored in ChromaDB, a persistent vector database.

4. **Query**: When you ask a question, it's converted to an embedding and used to find the most relevant document chunks.

5. **Generation**: Retrieved context is passed to the LLM (Ollama) along with your question to generate an answer.

## Troubleshooting

### Ollama Connection Issues

If you get connection errors:
- Make sure Ollama is running: `ollama serve`
- Check if models are pulled: `ollama list`

### Memory Issues

If you run out of memory:
- Use a smaller model: `--model tinyllama`
- Reduce context size by editing `n_context` in the chatbot

### Empty Responses

If the bot doesn't find relevant context:
- Make sure PDFs are loaded correctly
- Try rephrasing your question
- Check if the question is related to document content

## Contributing

Contributions are welcome! Please feel free to submit issues or pull requests.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

- [Ollama](https://ollama.ai/) - Local LLM inference
- [ChromaDB](https://www.trychroma.com/) - Vector database
- [LangChain](https://www.langchain.com/) - LLM framework
- [PyPDF](https://pypdf2.readthedocs.io/) - PDF processing