# Quick Start Guide

## Prerequisites Check

Before running the chatbot, make sure you have:

1. **Python 3.8+** installed
   ```bash
   python --version
   ```

2. **Ollama** installed and running
   ```bash
   # Check if Ollama is running
   ollama list
   ```

3. **Required models** downloaded
   ```bash
   # Download the chat model (choose one)
   ollama pull llama2          # Recommended for most systems
   ollama pull mistral         # Alternative option
   ollama pull tinyllama       # Lightweight option
   
   # Download the embedding model
   ollama pull nomic-embed-text
   ```

## Installation

1. Install Python dependencies:
   ```bash
   pip install -r requirements.txt
   ```

2. Verify installation:
   ```bash
   python test_components.py
   ```

## Usage Examples

### Example 1: Basic Usage with Sample PDF

```bash
# Run with the included sample PDF
python main.py
```

### Example 2: Load Your Own PDFs

```bash
# Place your PDFs in the data directory
cp /path/to/your/document.pdf data/

# Run the chatbot
python main.py
```

### Example 3: Load Specific PDF Files

```bash
# Load one or more specific PDF files
python main.py --pdfs research_paper.pdf textbook.pdf
```

### Example 4: Clear Existing Data and Reload

```bash
# Clear the vector store and reload PDFs
python main.py --clear --pdfs new_document.pdf
```

### Example 5: Use Different Models

```bash
# Use Mistral for chat and a different embedding model
python main.py --model mistral --embedding-model mxbai-embed-large
```

## Sample Questions to Try

With the included sample PDF about machine learning:

1. "What is machine learning?"
2. "What are the key topics covered in this course?"
3. "Explain supervised learning"
4. "What algorithms are mentioned for supervised learning?"
5. "What is a neural network?"
6. "What are activation functions?"

## Troubleshooting

### Issue: "Connection refused" or Ollama errors

**Solution:** Make sure Ollama is running:
```bash
# Start Ollama (if not running)
ollama serve
```

### Issue: "Model not found"

**Solution:** Pull the required models:
```bash
ollama pull llama2
ollama pull nomic-embed-text
```

### Issue: Slow responses

**Solutions:**
- Use a smaller model: `--model tinyllama`
- Reduce context: Edit `n_context=3` to `n_context=1` in main.py
- Use a faster embedding model

### Issue: Out of memory

**Solutions:**
- Use a smaller chat model: `ollama pull tinyllama`
- Close other applications
- Process fewer PDFs at once

## Advanced Configuration

### Customize the System Prompt

Edit `src/chatbot.py` and modify the prompt template in the `chat()` method.

### Change Chunk Size

For better performance with large documents, you can split pages into smaller chunks by modifying `src/pdf_loader.py`.

### Use Different Vector Store

The default is ChromaDB. To use a different vector store, modify `src/vector_store.py`.

## Project Structure

```
ai-course-chatbot/
├── src/
│   ├── __init__.py         # Package initialization
│   ├── pdf_loader.py       # PDF text extraction
│   ├── vector_store.py     # Vector database management
│   └── chatbot.py          # RAG chatbot logic
├── data/                   # Place your PDF files here
│   └── sample_course.pdf   # Sample PDF included
├── main.py                 # Main application
├── test_components.py      # Component tests
├── requirements.txt        # Python dependencies
└── README.md              # Full documentation
```

## Tips for Best Results

1. **Quality PDFs**: Use text-based PDFs, not scanned images
2. **Relevant Questions**: Ask specific questions about the document content
3. **Context**: The chatbot retrieves the 3 most relevant passages by default
4. **Sources**: Check the sources shown with each answer to verify accuracy

## Next Steps

- Add more PDFs to your `data/` directory
- Try different Ollama models
- Customize the prompt for your use case
- Integrate with your existing workflow

Enjoy using the AI Course Chatbot!
