"""
Services package for Document Intelligence Platform.

This package contains business logic services for:
- Document processing and management
- Search functionality
- User authentication and management
"""

from .document_service import process_document
from .search_service import build_index, search_documents
from .user_service import authenticate_user, get_user_role

__all__ = [
    "process_document",
    "build_index", 
    "search_documents",
    "authenticate_user",
    "get_user_role"
]