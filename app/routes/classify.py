"""
Document Classification API routes.

This module provides endpoints for classifying documents
into predefined categories.
"""

import logging
from datetime import datetime
from typing import Optional
from fastapi import APIRouter, HTTPException, Depends # type: ignore
from fastapi.responses import JSONResponse # type: ignore
from pydantic import BaseModel # type: ignore

from app.models.classifier_model import classify_document
from app.services.document_service import get_document_by_id
from app.services.user_service import get_current_user
from app.utils.logger import log_api_call

logger = logging.getLogger(__name__)

router = APIRouter()


class ClassifyRequest(BaseModel):
    """Request model for classification."""
    text: str
    return_all_scores: Optional[bool] = False


@router.post("/classify")
async def classify_text_endpoint(
    request: ClassifyRequest,
    current_user: Optional[dict] = Depends(get_current_user)
):
    """
    Classify text into document categories.
    
    Args:
        request: Classification request with text
        current_user: Current authenticated user (optional)
        
    Returns:
        JSONResponse: Classification results
    """
    start_time = datetime.now()
    user_id = current_user.get("user_id") if current_user else None
    
    try:
        if not request.text or not request.text.strip():
            raise HTTPException(status_code=400, detail="Text cannot be empty")
        
        # Classify document
        result = classify_document(request.text, request.return_all_scores)
        
        # Log API call
        processing_time = (datetime.now() - start_time).total_seconds()
        log_api_call(
            endpoint="/classify",
            method="POST",
            user_id=user_id,
            request_data={"text_length": len(request.text)},
            response_status=200,
            processing_time=processing_time
        )
        
        return JSONResponse(
            content={
                "classification_result": result,
                "processing_time_seconds": processing_time,
                "timestamp": datetime.now().isoformat()
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        processing_time = (datetime.now() - start_time).total_seconds()
        logger.error(f"Classification failed: {str(e)}")
        
        log_api_call(
            endpoint="/classify",
            method="POST",
            user_id=user_id,
            response_status=500,
            processing_time=processing_time
        )
        
        raise HTTPException(status_code=500, detail=f"Classification failed: {str(e)}")


@router.get("/classify/{document_id}")
async def get_document_classification(
    document_id: str,
    current_user: Optional[dict] = Depends(get_current_user)
):
    """
    Get classification of a processed document.
    
    Args:
        document_id: Document ID
        current_user: Current authenticated user (optional)
        
    Returns:
        JSONResponse: Document classification
    """
    try:
        document = get_document_by_id(document_id)
        if not document:
            raise HTTPException(status_code=404, detail="Document not found")
        
        classification = document.get("classification", {})
        
        return JSONResponse(
            content={
                "document_id": document_id,
                "document_name": document.get("file_name", "Unknown"),
                "classification": classification,
                "processing_timestamp": document.get("processing_timestamp", ""),
                "timestamp": datetime.now().isoformat()
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get document classification: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to retrieve document classification")