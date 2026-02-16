# Quick Start Guide

This guide will help you get the AI RAG Chatbot up and running in minutes.

## Step 1: Prerequisites

### Install Ollama

1. Visit https://ollama.ai and download Ollama for your operating system
2. Install and start Ollama
3. Pull required models:

```bash
ollama pull gemma3:4b
ollama pull nomic-embed-text
```

Verify Ollama is running:
```bash
ollama list
```

You should see both models listed.

## Step 2: Setup Python Environment

1. Clone the repository:
```bash
git clone https://github.com/lersam/ai-course-chatbot.git
cd ai-course-chatbot
```

2. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

## Step 3: Ingest Your PDFs

Build (or rebuild) the Chroma vector store using the ingestion helper. Pass every PDF you want available in the chatbot:

```bash
python ai_course_chatbot/setup_vector_store.py --pdf doc1.pdf doc2.pdf doc3.pdf
```

> The helper reuses the existing persisted Chroma collection, appending new content and deduplicating existing entries. Rerun this command whenever you add or update documents so the changes are reflected in the chatbot.

## Step 4: Start the Web Server

Launch the FastAPI service and open the chat UI in your browser:

```bash
uvicorn ai_course_chatbot.main:app --host 0.0.0.0 --port 8000 --reload
# then browse to http://localhost:8000
```

The server preloads the vector store you created in Step 3 and serves the chat interface at `/`.

## Step 5: Chat with Your Documents

Once the chatbot starts, you'll see:

```
============================================================
AI RAG Chatbot (Model: gemma3:4b)
============================================================
Type 'quit' or 'exit' to end the conversation.

You: 
```

Ask questions about your documents:

```
You: What is the main topic of this document?
Chatbot: [Answer based on your PDF content]

Sources:
1. your_document.pdf (Page 1)

You: Can you summarize the key points?
Chatbot: [Summary of key points]

You: exit
Goodbye!
```

## Advanced Usage

### Use a Different Model

Set `OLLAMA_MODEL` before starting the FastAPI server to override the default `gemma3:4b` (be sure to `ollama pull` the model first):

```bash
export OLLAMA_MODEL=gemma3:2b-instruct
uvicorn ai_course_chatbot.main:app --host 0.0.0.0 --port 8000 --reload
```

### Rebuild the Vector Store

Whenever PDFs change, rerun the ingestion helper with the updated file list:

```bash
python ai_course_chatbot/setup_vector_store.py --pdf updated.pdf more.pdf
```

## Troubleshooting

### "Connection refused" or Ollama errors
- Make sure Ollama is running: `ollama serve`
- Check models are installed: `ollama list`

### "Module not found" errors
- Activate your virtual environment
- Reinstall dependencies: `pip install -r requirements.txt`

### No answer or slow responses
- First query might be slow (loading model)
- Try a different model (e.g., mistral, llama3)
- Ensure your PDF has extractable text

## What's Next?

- Customize chunk size in `pdf_loader.py` for better results
- Adjust temperature in `rag_chatbot.py` for more creative/conservative answers
- Add more documents to build a larger knowledge base
- Explore programmatic usage with `example.py`

## Getting Help

If you encounter issues:
1. Check the main README.md for detailed documentation
2. Verify Ollama is running and models are downloaded
3. Check that your PDF has readable text (not scanned images)
4. Open an issue on GitHub with error details

Happy chatting! 🤖📚
