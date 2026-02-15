# Quick Start Guide

This guide will help you get the AI RAG Chatbot up and running in minutes.

## Step 1: Prerequisites

### Install Ollama

1. Visit https://ollama.ai and download Ollama for your operating system
2. Install and start Ollama
3. Pull required models:

```bash
ollama pull gemma3:4b
ollama pull qwen3-embedding:4b
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

## Step 3: Run the Chatbot

### First Time - Load a PDF

```bash
python main.py --pdf your_document.pdf
```

Replace `your_document.pdf` with the path to your PDF file.

### Subsequent Runs

After the first run, the vector store is saved, so you can start chatting without reloading:

```bash
python main.py
```

### Load Multiple PDFs

```bash
python main.py --pdf doc1.pdf doc2.pdf doc3.pdf
```

## Step 4: Chat with Your Documents

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

```bash
python main.py --pdf document.pdf --model mistral
```

Make sure to pull the model first:
```bash
ollama pull mistral
```

### Force Reload PDFs

If you've updated your PDFs and want to reload them:

```bash
python main.py --pdf document.pdf --reload
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
