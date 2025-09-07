"""
Additional API routes for document management and statistics.
"""

import logging
import json
from pathlib import Path
from typing import List, Dict, Any
from fastapi import APIRouter, HTTPException # type: ignore
from fastapi.responses import JSONResponse # type: ignore

from app.config import settings

logger = logging.getLogger(__name__)
router = APIRouter()

@router.get("/documents")
async def get_documents():
    """Get list of all processed documents."""
    try:
        processed_files = list(settings.PROCESSED_FOLDER.glob("*.json"))
        documents = []
        
        for file_path in processed_files:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    doc_data = json.load(f)
                    documents.append({
                        "document_id": doc_data.get("document_id"),
                        "file_name": doc_data.get("file_name"),
                        "file_size": doc_data.get("file_size"),
                        "file_size_bytes": doc_data.get("file_size"),
                        "classification": doc_data.get("classification"),
                        "entity_count": len(doc_data.get("entities", {}).get("PERSON", [])) + 
                                       len(doc_data.get("entities", {}).get("ORG", [])) + 
                                       len(doc_data.get("entities", {}).get("LOCATION", [])),
                        "text_length": len(doc_data.get("raw_text", doc_data.get("text", ""))),
                        "processing_timestamp": doc_data.get("processing_timestamp"),
                        "summary": doc_data.get("summary", "")[:200] + "..." if len(doc_data.get("summary", "")) > 200 else doc_data.get("summary", "")
                    })
            except Exception as e:
                logger.error(f"Error reading document {file_path}: {e}")
                continue
        
        return JSONResponse({
            "documents": documents,
            "total": len(documents)
        })
        
    except Exception as e:
        logger.error(f"Error fetching documents: {e}")
        return JSONResponse({
            "documents": [],
            "total": 0
        })

@router.get("/stats")
async def get_stats():
    """Get platform statistics."""
    try:
        processed_files = list(settings.PROCESSED_FOLDER.glob("*.json"))
        upload_files = list(settings.UPLOAD_FOLDER.glob("*"))
        
        categories = {}
        total_processing_time = 0
        valid_docs = 0
        
        for file_path in processed_files:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    doc_data = json.load(f)
                    
                    # Count categories
                    category = doc_data.get("classification", {}).get("category", "unknown")
                    categories[category] = categories.get(category, 0) + 1
                    
                    # Sum processing times
                    if "processing_time_seconds" in doc_data:
                        total_processing_time += doc_data["processing_time_seconds"]
                        valid_docs += 1
                        
            except Exception as e:
                logger.error(f"Error reading stats from {file_path}: {e}")
                continue
        
        avg_processing_time = total_processing_time / valid_docs if valid_docs > 0 else 0
        
        return JSONResponse({
            "total_documents": len(processed_files),
            "uploaded_files": len(upload_files),
            "categories": categories,
            "average_processing_time": round(avg_processing_time, 2)
        })
        
    except Exception as e:
        logger.error(f"Error fetching stats: {e}")
        return JSONResponse({
            "total_documents": 0,
            "uploaded_files": 0,
            "categories": {},
            "average_processing_time": 0
        })

@router.get("/documents/{document_id}")
async def get_document_by_id(document_id: str):
    """Get full details of a specific document by ID."""
    try:
        # Search for the document file in processed folder
        processed_files = list(settings.PROCESSED_FOLDER.glob("*.json"))
        
        for file_path in processed_files:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    doc_data = json.load(f)
                    
                    if doc_data.get("document_id") == document_id:
                        # Return full document data (not truncated)
                        return JSONResponse(doc_data)
                        
            except Exception as e:
                logger.error(f"Error reading document {file_path}: {e}")
                continue
        
        # Document not found
        raise HTTPException(status_code=404, detail=f"Document with ID {document_id} not found")
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching document {document_id}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")
