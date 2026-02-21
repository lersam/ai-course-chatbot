"""
Configuration constants for the AI Course Chatbot
"""
import os
import tempfile

# Use the system default temporary directory for downloaded PDFs
DOWNLOAD_DIR = os.path.join(tempfile.gettempdir(), "ai-course-chatbot", "downloads")
