"""
Routes package for Document Intelligence Platform.

This package contains all API route handlers for:
- File upload and processing
- Text summarization
- Named entity recognition
- Document search
- Document classification
"""

from . import upload, summarize, ner, search, classify

__all__ = ["upload", "summarize", "ner", "search", "classify"]