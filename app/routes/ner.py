"""
Named Entity Recognition (NER) API routes.

This module provides endpoints for extracting named entities
from text and documents.
"""

import logging
from datetime import datetime
from typing import Optional
from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from app.models.ner_model import extract_entities, extract_entities_with_positions, get_entity_statistics
from app.services.document_service import get_document_by_id
from app.services.user_service import get_current_user
from app.utils.logger import log_api_call

logger = logging.getLogger(__name__)

router = APIRouter()


class NERRequest(BaseModel):
    """Request model for NER."""
    text: str


@router.post("/ner")
async def extract_entities_endpoint(
    request: NERRequest,
    current_user: Optional[dict] = Depends(get_current_user)
):
    """
    Extract named entities from text.
    
    Args:
        request: NER request with text
        current_user: Current authenticated user (optional)
        
    Returns:
        JSONResponse: Extracted entities
    """
    start_time = datetime.now()
    user_id = current_user.get("user_id") if current_user else None
    
    try:
        if not request.text or not request.text.strip():
            raise HTTPException(status_code=400, detail="Text cannot be empty")
        
        # Extract entities
        entities = extract_entities(request.text)
        entities_with_positions = extract_entities_with_positions(request.text)
        stats = get_entity_statistics(entities)
        
        # Log API call
        processing_time = (datetime.now() - start_time).total_seconds()
        log_api_call(
            endpoint="/ner",
            method="POST",
            user_id=user_id,
            request_data={"text_length": len(request.text)},
            response_status=200,
            processing_time=processing_time
        )
        
        return JSONResponse(
            content={
                "entities": entities,
                "entities_with_positions": entities_with_positions,
                "statistics": stats,
                "processing_time_seconds": processing_time,
                "timestamp": datetime.now().isoformat()
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        processing_time = (datetime.now() - start_time).total_seconds()
        logger.error(f"NER failed: {str(e)}")
        
        log_api_call(
            endpoint="/ner",
            method="POST",
            user_id=user_id,
            response_status=500,
            processing_time=processing_time
        )
        
        raise HTTPException(status_code=500, detail=f"NER failed: {str(e)}")


@router.get("/ner/{document_id}")
async def get_document_entities(
    document_id: str,
    current_user: Optional[dict] = Depends(get_current_user)
):
    """
    Get entities from a processed document.
    
    Args:
        document_id: Document ID
        current_user: Current authenticated user (optional)
        
    Returns:
        JSONResponse: Document entities
    """
    try:
        document = get_document_by_id(document_id)
        if not document:
            raise HTTPException(status_code=404, detail="Document not found")
        
        entities = document.get("entities", {})
        entity_count = document.get("entity_count", 0)
        
        return JSONResponse(
            content={
                "document_id": document_id,
                "document_name": document.get("file_name", "Unknown"),
                "entities": entities,
                "entity_count": entity_count,
                "processing_timestamp": document.get("processing_timestamp", ""),
                "timestamp": datetime.now().isoformat()
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get document entities: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to retrieve document entities")