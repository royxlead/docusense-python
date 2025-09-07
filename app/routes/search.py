"""
Document search API routes.

This module provides endpoints for semantic document search
using vector embeddings and similarity matching.
"""

import logging
from datetime import datetime
from typing import Optional, List
from fastapi import APIRouter, HTTPException, Query, Depends
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from app.services.search_service import search_documents, get_similar_documents, get_search_statistics
from app.services.user_service import get_current_user
from app.utils.logger import log_api_call

logger = logging.getLogger(__name__)

router = APIRouter()


class SearchRequest(BaseModel):
    """Request model for document search."""
    query: str
    k: Optional[int] = 5
    category_filter: Optional[str] = None
    min_similarity: Optional[float] = 0.1


@router.get("/search")
async def search_documents_endpoint(
    query: str = Query(..., description="Search query text"),
    k: int = Query(5, description="Number of results to return"),
    category_filter: Optional[str] = Query(None, description="Filter by document category"),
    min_similarity: float = Query(0.1, description="Minimum similarity threshold"),
    current_user: Optional[dict] = Depends(get_current_user)
):
    """
    Search for documents using semantic similarity.
    
    This endpoint performs semantic search across all processed documents
    using vector embeddings and returns the most similar documents.
    
    Args:
        query: Search query text
        k: Number of results to return
        category_filter: Optional category filter
        min_similarity: Minimum similarity threshold
        current_user: Current authenticated user (optional)
        
    Returns:
        JSONResponse: Search results with similarity scores
    """
    start_time = datetime.now()
    user_id = current_user.get("user_id") if current_user else None
    
    try:
        logger.info(f"Search query: '{query}' (k={k})")
        
        # Validate input
        if not query or not query.strip():
            raise HTTPException(status_code=400, detail="Query cannot be empty")
        
        if len(query) > 1000:
            raise HTTPException(status_code=400, detail="Query too long (maximum 1000 characters)")
        
        if k < 1 or k > 50:
            raise HTTPException(status_code=400, detail="k must be between 1 and 50")
        
        # Perform search
        results = search_documents(
            query=query,
            k=k,
            user_id=user_id,
            category_filter=category_filter,
            min_similarity=min_similarity
        )
        
        # Log API call
        processing_time = (datetime.now() - start_time).total_seconds()
        log_api_call(
            endpoint="/search",
            method="GET",
            user_id=user_id,
            request_data={
                "query": query[:100],  # Truncate long queries for logging
                "k": k,
                "category_filter": category_filter
            },
            response_status=200,
            processing_time=processing_time
        )
        
        return JSONResponse(
            content={
                "query": query,
                "results": results,
                "total_results": len(results),
                "search_parameters": {
                    "k": k,
                    "category_filter": category_filter,
                    "min_similarity": min_similarity
                },
                "processing_time_seconds": processing_time,
                "timestamp": datetime.now().isoformat()
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        processing_time = (datetime.now() - start_time).total_seconds()
        logger.error(f"Search failed: {str(e)}")
        
        log_api_call(
            endpoint="/search",
            method="GET",
            user_id=user_id,
            response_status=500,
            processing_time=processing_time
        )
        
        raise HTTPException(status_code=500, detail=f"Search failed: {str(e)}")


@router.post("/search")
async def search_documents_post(
    request: SearchRequest,
    current_user: Optional[dict] = Depends(get_current_user)
):
    """
    Search for documents using POST method (for complex queries).
    
    Args:
        request: Search request with query and parameters
        current_user: Current authenticated user (optional)
        
    Returns:
        JSONResponse: Search results
    """
    start_time = datetime.now()
    user_id = current_user.get("user_id") if current_user else None
    
    try:
        # Validate input
        if not request.query or not request.query.strip():
            raise HTTPException(status_code=400, detail="Query cannot be empty")
        
        # Perform search
        results = search_documents(
            query=request.query,
            k=request.k,
            user_id=user_id,
            category_filter=request.category_filter,
            min_similarity=request.min_similarity
        )
        
        # Log API call
        processing_time = (datetime.now() - start_time).total_seconds()
        log_api_call(
            endpoint="/search",
            method="POST",
            user_id=user_id,
            request_data={"query_length": len(request.query), "k": request.k},
            response_status=200,
            processing_time=processing_time
        )
        
        return JSONResponse(
            content={
                "query": request.query,
                "results": results,
                "total_results": len(results),
                "processing_time_seconds": processing_time,
                "timestamp": datetime.now().isoformat()
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        processing_time = (datetime.now() - start_time).total_seconds()
        logger.error(f"Search POST failed: {str(e)}")
        
        log_api_call(
            endpoint="/search",
            method="POST",
            user_id=user_id,
            response_status=500,
            processing_time=processing_time
        )
        
        raise HTTPException(status_code=500, detail=f"Search failed: {str(e)}")


@router.get("/similar/{document_id}")
async def get_similar_documents_endpoint(
    document_id: str,
    k: int = Query(5, description="Number of similar documents to return"),
    current_user: Optional[dict] = Depends(get_current_user)
):
    """
    Find documents similar to a given document.
    
    Args:
        document_id: ID of the reference document
        k: Number of similar documents to return
        current_user: Current authenticated user (optional)
        
    Returns:
        JSONResponse: Similar documents
    """
    start_time = datetime.now()
    user_id = current_user.get("user_id") if current_user else None
    
    try:
        logger.info(f"Finding similar documents for: {document_id}")
        
        # Validate input
        if not document_id or not document_id.strip():
            raise HTTPException(status_code=400, detail="Document ID cannot be empty")
        
        if k < 1 or k > 20:
            raise HTTPException(status_code=400, detail="k must be between 1 and 20")
        
        # Find similar documents
        similar_docs = get_similar_documents(document_id, k)
        
        if not similar_docs:
            raise HTTPException(status_code=404, detail="Document not found or no similar documents available")
        
        # Log API call
        processing_time = (datetime.now() - start_time).total_seconds()
        log_api_call(
            endpoint=f"/similar/{document_id}",
            method="GET",
            user_id=user_id,
            request_data={"document_id": document_id, "k": k},
            response_status=200,
            processing_time=processing_time
        )
        
        return JSONResponse(
            content={
                "reference_document_id": document_id,
                "similar_documents": similar_docs,
                "total_similar": len(similar_docs),
                "processing_time_seconds": processing_time,
                "timestamp": datetime.now().isoformat()
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        processing_time = (datetime.now() - start_time).total_seconds()
        logger.error(f"Similar documents search failed: {str(e)}")
        
        log_api_call(
            endpoint=f"/similar/{document_id}",
            method="GET",
            user_id=user_id,
            response_status=500,
            processing_time=processing_time
        )
        
        raise HTTPException(status_code=500, detail=f"Similar documents search failed: {str(e)}")


@router.get("/search-stats")
async def get_search_stats(
    current_user: Optional[dict] = Depends(get_current_user)
):
    """
    Get search index statistics.
    
    Args:
        current_user: Current authenticated user (optional)
        
    Returns:
        JSONResponse: Search statistics
    """
    try:
        stats = get_search_statistics()
        
        return JSONResponse(
            content={
                "search_statistics": stats,
                "timestamp": datetime.now().isoformat()
            }
        )
        
    except Exception as e:
        logger.error(f"Failed to get search statistics: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to retrieve search statistics")


@router.post("/rebuild-index")
async def rebuild_search_index(
    current_user: dict = Depends(get_current_user)
):
    """
    Rebuild the search index (admin only).
    
    Args:
        current_user: Current authenticated user
        
    Returns:
        JSONResponse: Rebuild status
    """
    try:
        # Check admin permissions
        if current_user.get("role") != "admin":
            raise HTTPException(status_code=403, detail="Admin access required")
        
        from app.services.search_service import refresh_index
        
        logger.info(f"Search index rebuild initiated by: {current_user.get('username')}")
        
        success = refresh_index()
        
        if success:
            return JSONResponse(
                content={
                    "message": "Search index rebuilt successfully",
                    "timestamp": datetime.now().isoformat()
                }
            )
        else:
            raise HTTPException(status_code=500, detail="Failed to rebuild search index")
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Index rebuild failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Index rebuild failed: {str(e)}")