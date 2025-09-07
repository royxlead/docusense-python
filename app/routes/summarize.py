"""
Summarization API routes.

This module provides endpoints for text and document summarization
using AI models.
"""

import logging
from datetime import datetime
from typing import Optional
from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from app.models.summarization_model import summarize_text, get_summary_statistics
from app.services.document_service import get_document_by_id
from app.services.user_service import get_current_user
from app.utils.logger import log_api_call

logger = logging.getLogger(__name__)

router = APIRouter()


class SummarizeRequest(BaseModel):
    """Request model for text summarization."""
    text: str
    max_length: Optional[int] = 150
    min_length: Optional[int] = 50


class SummarizeDocumentRequest(BaseModel):
    """Request model for document summarization."""
    document_id: str
    max_length: Optional[int] = 150
    min_length: Optional[int] = 50


@router.post("/summarize")
async def summarize_text_endpoint(
    request: SummarizeRequest,
    current_user: Optional[dict] = Depends(get_current_user)
):
    """
    Summarize provided text.
    
    This endpoint takes raw text and generates a concise summary
    using AI-powered summarization models.
    
    Args:
        request: Summarization request with text and parameters
        current_user: Current authenticated user (optional)
        
    Returns:
        JSONResponse: Summarization results
    """
    start_time = datetime.now()
    user_id = current_user.get("user_id") if current_user else None
    
    try:
        logger.info(f"Text summarization requested (length: {len(request.text)})")
        
        # Validate input
        if not request.text or not request.text.strip():
            raise HTTPException(status_code=400, detail="Text cannot be empty")
        
        if len(request.text) < 50:
            raise HTTPException(status_code=400, detail="Text too short for summarization (minimum 50 characters)")
        
        if len(request.text) > 50000:
            raise HTTPException(status_code=400, detail="Text too long (maximum 50,000 characters)")
        
        # Generate summary
        summary = summarize_text(
            request.text,
            max_length=request.max_length,
            min_length=request.min_length
        )
        
        # Calculate statistics
        stats = get_summary_statistics(request.text, summary)
        
        # Log API call
        processing_time = (datetime.now() - start_time).total_seconds()
        log_api_call(
            endpoint="/summarize",
            method="POST",
            user_id=user_id,
            request_data={
                "text_length": len(request.text),
                "max_length": request.max_length,
                "min_length": request.min_length
            },
            response_status=200,
            processing_time=processing_time
        )
        
        return JSONResponse(
            content={
                "summary": summary,
                "original_text_length": len(request.text),
                "summary_length": len(summary),
                "statistics": stats,
                "processing_time_seconds": processing_time,
                "timestamp": datetime.now().isoformat()
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        processing_time = (datetime.now() - start_time).total_seconds()
        logger.error(f"Summarization failed: {str(e)}")
        
        log_api_call(
            endpoint="/summarize",
            method="POST",
            user_id=user_id,
            response_status=500,
            processing_time=processing_time
        )
        
        raise HTTPException(status_code=500, detail=f"Summarization failed: {str(e)}")


@router.post("/summarize-document")
async def summarize_document_endpoint(
    request: SummarizeDocumentRequest,
    current_user: Optional[dict] = Depends(get_current_user)
):
    """
    Summarize a processed document by ID.
    
    This endpoint retrieves a document by its ID and generates
    a fresh summary or returns the existing one.
    
    Args:
        request: Document summarization request
        current_user: Current authenticated user (optional)
        
    Returns:
        JSONResponse: Document summarization results
    """
    start_time = datetime.now()
    user_id = current_user.get("user_id") if current_user else None
    
    try:
        logger.info(f"Document summarization requested for ID: {request.document_id}")
        
        # Get document
        document = get_document_by_id(request.document_id)
        if not document:
            raise HTTPException(status_code=404, detail="Document not found")
        
        # Check if user has access to this document
        if current_user and document.get("user_id") and document.get("user_id") != user_id:
            if current_user.get("role") != "admin":
                raise HTTPException(status_code=403, detail="Access denied to this document")
        
        # Get document text
        document_text = document.get("raw_text", "")
        if not document_text:
            raise HTTPException(status_code=400, detail="Document has no extractable text")
        
        # Generate new summary or return existing one
        existing_summary = document.get("summary", "")
        
        if existing_summary and len(existing_summary) > 10:
            # Return existing summary
            summary = existing_summary
            logger.info("Returned existing summary")
        else:
            # Generate new summary
            summary = summarize_text(
                document_text,
                max_length=request.max_length,
                min_length=request.min_length
            )
            logger.info("Generated new summary")
        
        # Calculate statistics
        stats = get_summary_statistics(document_text, summary)
        
        # Log API call
        processing_time = (datetime.now() - start_time).total_seconds()
        log_api_call(
            endpoint="/summarize-document",
            method="POST",
            user_id=user_id,
            request_data={"document_id": request.document_id},
            response_status=200,
            processing_time=processing_time
        )
        
        return JSONResponse(
            content={
                "document_id": request.document_id,
                "document_name": document.get("file_name", "Unknown"),
                "summary": summary,
                "is_existing_summary": existing_summary == summary,
                "original_text_length": len(document_text),
                "summary_length": len(summary),
                "statistics": stats,
                "document_classification": document.get("classification", {}),
                "processing_time_seconds": processing_time,
                "timestamp": datetime.now().isoformat()
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        processing_time = (datetime.now() - start_time).total_seconds()
        logger.error(f"Document summarization failed: {str(e)}")
        
        log_api_call(
            endpoint="/summarize-document",
            method="POST",
            user_id=user_id,
            response_status=500,
            processing_time=processing_time
        )
        
        raise HTTPException(status_code=500, detail=f"Document summarization failed: {str(e)}")


@router.get("/summary/{document_id}")
async def get_document_summary(
    document_id: str,
    current_user: Optional[dict] = Depends(get_current_user)
):
    """
    Get the existing summary of a document.
    
    Args:
        document_id: ID of the document
        current_user: Current authenticated user (optional)
        
    Returns:
        JSONResponse: Document summary
    """
    try:
        # Get document
        document = get_document_by_id(document_id)
        if not document:
            raise HTTPException(status_code=404, detail="Document not found")
        
        # Check access permissions
        user_id = current_user.get("user_id") if current_user else None
        if current_user and document.get("user_id") and document.get("user_id") != user_id:
            if current_user.get("role") != "admin":
                raise HTTPException(status_code=403, detail="Access denied to this document")
        
        summary = document.get("summary", "")
        if not summary:
            raise HTTPException(status_code=404, detail="No summary available for this document")
        
        # Calculate basic statistics
        original_text = document.get("raw_text", "")
        stats = get_summary_statistics(original_text, summary) if original_text else {}
        
        return JSONResponse(
            content={
                "document_id": document_id,
                "document_name": document.get("file_name", "Unknown"),
                "summary": summary,
                "statistics": stats,
                "classification": document.get("classification", {}),
                "processing_timestamp": document.get("processing_timestamp", ""),
                "timestamp": datetime.now().isoformat()
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get document summary: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to retrieve document summary")


@router.get("/summaries")
async def list_document_summaries(
    limit: int = 20,
    offset: int = 0,
    current_user: Optional[dict] = Depends(get_current_user)
):
    """
    List summaries of all documents.
    
    Args:
        limit: Maximum number of summaries to return
        offset: Number of summaries to skip
        current_user: Current authenticated user (optional)
        
    Returns:
        JSONResponse: List of document summaries
    """
    try:
        from app.services.document_service import list_documents
        
        # Get user filter
        user_filter = None
        if current_user and current_user.get("role") != "admin":
            user_filter = current_user.get("user_id")
        
        # Get documents
        documents = list_documents(user_id=user_filter, limit=limit, offset=offset)
        
        # Extract summaries
        summaries = []
        for doc in documents:
            if doc.get("summary"):
                summary_info = {
                    "document_id": doc.get("document_id"),
                    "document_name": doc.get("file_name", "Unknown"),
                    "summary": doc.get("summary", "")[:200] + "..." if len(doc.get("summary", "")) > 200 else doc.get("summary", ""),
                    "full_summary_length": len(doc.get("summary", "")),
                    "classification": doc.get("classification", {}),
                    "processing_timestamp": doc.get("processing_timestamp", ""),
                    "text_length": doc.get("text_length", 0)
                }
                summaries.append(summary_info)
        
        return JSONResponse(
            content={
                "summaries": summaries,
                "total_summaries": len(summaries),
                "limit": limit,
                "offset": offset,
                "timestamp": datetime.now().isoformat()
            }
        )
        
    except Exception as e:
        logger.error(f"Failed to list summaries: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to list document summaries")