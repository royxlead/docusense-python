"""
Document processing service.

This module provides functions to handle document upload, processing,
and management including OCR, analysis, and storage operations.
"""

import logging
import os
import uuid
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional, List
import json
import hashlib

from app.config import settings
from app.models.ocr_model import extract_text_from_pdf
from app.models.summarization_model import summarize_text
from app.models.ner_model import extract_entities
from app.models.classifier_model import classify_document
from app.models.classifier_model import classify_document
from app.models.embedding_model import generate_embedding
from app.utils.logger import log_document_processing
from app.utils.preprocessing import clean_text, get_text_statistics

logger = logging.getLogger(__name__)


def process_document(file_path: str, user_id: Optional[str] = None) -> Dict[str, Any]:
    """
    Process a document through the complete AI pipeline.
    
    This function takes a document file and runs it through OCR,
    summarization, NER, classification, and embedding generation.
    
    Args:
        file_path: Path to the document file to process
        user_id: ID of the user uploading the document
        
    Returns:
        Dict[str, Any]: Complete processing results including:
            - document_id: Unique identifier
            - raw_text: Extracted text
            - summary: Document summary
            - entities: Named entities
            - classification: Document category and confidence
            - embedding: Vector embedding
            - metadata: Processing metadata
            
    Raises:
        FileNotFoundError: If the file doesn't exist
        Exception: If processing fails
    """
    start_time = datetime.now()
    document_id = str(uuid.uuid4())
    
    try:
        file_path = Path(file_path)
        
        if not file_path.exists():
            raise FileNotFoundError(f"Document file not found: {file_path}")
        
        logger.info(f"Starting document processing: {file_path}")
        log_document_processing(document_id, str(file_path), "started", "processing")
        
        # Initialize result structure
        result = {
            "document_id": document_id,
            "file_path": str(file_path),
            "file_name": file_path.name,
            "file_size": file_path.stat().st_size,
            "user_id": user_id,
            "processing_timestamp": start_time.isoformat(),
            "status": "processing"
        }
        
        # Step 1: OCR - Extract text from document
        logger.info(f"Step 1: OCR processing for {document_id}")
        ocr_start = datetime.now()
        
        try:
            raw_text = extract_text_from_pdf(str(file_path))
            result["raw_text"] = raw_text
            result["text_length"] = len(raw_text)
            
            ocr_time = (datetime.now() - ocr_start).total_seconds()
            log_document_processing(document_id, str(file_path), "ocr", "completed", ocr_time)
            
        except Exception as e:
            logger.error(f"OCR failed for {document_id}: {e}")
            log_document_processing(document_id, str(file_path), "ocr", "failed", error_message=str(e))
            result["raw_text"] = "OCR processing failed"
            result["text_length"] = 0
        
        # Step 2: Text preprocessing and statistics
        if result["raw_text"]:
            cleaned_text = clean_text(result["raw_text"])
            text_stats = get_text_statistics(cleaned_text)
            result["text_statistics"] = text_stats
        
        # Step 3: Summarization
        logger.info(f"Step 2: Summarization for {document_id}")
        summary_start = datetime.now()
        
        try:
            if result["raw_text"] and len(result["raw_text"].strip()) > 50:
                summary = summarize_text(result["raw_text"])
                result["summary"] = summary
            else:
                result["summary"] = "Document too short for summarization"
            
            summary_time = (datetime.now() - summary_start).total_seconds()
            log_document_processing(document_id, str(file_path), "summarization", "completed", summary_time)
            
        except Exception as e:
            logger.error(f"Summarization failed for {document_id}: {e}")
            log_document_processing(document_id, str(file_path), "summarization", "failed", error_message=str(e))
            result["summary"] = "Summarization failed"
        
        # Step 4: Named Entity Recognition
        logger.info(f"Step 3: NER processing for {document_id}")
        ner_start = datetime.now()
        
        try:
            if result["raw_text"]:
                entities = extract_entities(result["raw_text"])
                result["entities"] = entities
                result["entity_count"] = sum(len(v) for v in entities.values())
            else:
                result["entities"] = {}
                result["entity_count"] = 0
            
            ner_time = (datetime.now() - ner_start).total_seconds()
            log_document_processing(document_id, str(file_path), "ner", "completed", ner_time)
            
        except Exception as e:
            logger.error(f"NER failed for {document_id}: {e}")
            log_document_processing(document_id, str(file_path), "ner", "failed", error_message=str(e))
            result["entities"] = {}
            result["entity_count"] = 0
        
        # Step 5: Classification
        logger.info(f"Step 4: Classification for {document_id}")
        classification_start = datetime.now()
        
        try:
            if result["raw_text"]:
                # Use the main classifier (Gemini with fallback)
                classification = classify_document(result["raw_text"])
                logger.info(f"Document classification successful: {classification['category']}")
                result["classification"] = classification
            else:
                result["classification"] = {"category": "unknown", "confidence": 0.0}
            
            classification_time = (datetime.now() - classification_start).total_seconds()
            log_document_processing(document_id, str(file_path), "classification", "completed", classification_time)
            
        except Exception as e:
            logger.error(f"Classification failed for {document_id}: {e}")
            log_document_processing(document_id, str(file_path), "classification", "failed", error_message=str(e))
            result["classification"] = {"category": "unknown", "confidence": 0.0}
        
        # Step 6: Embedding generation
        logger.info(f"Step 5: Embedding generation for {document_id}")
        embedding_start = datetime.now()
        
        try:
            if result["raw_text"]:
                # Use summary for embedding if available, otherwise use truncated text
                text_for_embedding = result.get("summary", result["raw_text"][:1000])
                embedding = generate_embedding(text_for_embedding)
                result["embedding"] = embedding.tolist()  # Convert numpy to list for JSON
                result["embedding_dim"] = len(embedding)
            else:
                result["embedding"] = []
                result["embedding_dim"] = 0
            
            embedding_time = (datetime.now() - embedding_start).total_seconds()
            log_document_processing(document_id, str(file_path), "embedding", "completed", embedding_time)
            
        except Exception as e:
            logger.error(f"Embedding generation failed for {document_id}: {e}")
            log_document_processing(document_id, str(file_path), "embedding", "failed", error_message=str(e))
            result["embedding"] = []
            result["embedding_dim"] = 0
        
        # Calculate total processing time
        total_time = (datetime.now() - start_time).total_seconds()
        result["processing_time_seconds"] = total_time
        result["status"] = "completed"
        
        # Save processed document
        saved_path = save_processed_document(result)
        result["processed_file_path"] = saved_path
        
        logger.info(f"Document processing completed for {document_id} in {total_time:.2f}s")
        log_document_processing(document_id, str(file_path), "complete", "completed", total_time)
        
        return result
        
    except Exception as e:
        total_time = (datetime.now() - start_time).total_seconds()
        logger.error(f"Document processing failed for {document_id}: {str(e)}")
        log_document_processing(document_id, str(file_path), "complete", "failed", total_time, str(e))
        
        # Return partial results with error information
        return {
            "document_id": document_id,
            "file_path": str(file_path),
            "status": "failed",
            "error": str(e),
            "processing_time_seconds": total_time,
            "processing_timestamp": start_time.isoformat()
        }


def save_processed_document(result: Dict[str, Any]) -> str:
    """
    Save processed document results to storage.
    
    Args:
        result: Processing results dictionary
        
    Returns:
        str: Path to saved file
    """
    try:
        # Create processed data filename
        document_id = result["document_id"]
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{document_id}_{timestamp}.json"
        
        processed_path = settings.PROCESSED_FOLDER / filename
        
        # Save as JSON
        with open(processed_path, 'w', encoding='utf-8') as f:
            json.dump(result, f, indent=2, ensure_ascii=False)
        
        logger.info(f"Processed document saved to: {processed_path}")
        return str(processed_path)
        
    except Exception as e:
        logger.error(f"Failed to save processed document: {e}")
        return ""


def get_document_by_id(document_id: str) -> Optional[Dict[str, Any]]:
    """
    Retrieve a processed document by its ID.
    
    Args:
        document_id: Unique document identifier
        
    Returns:
        Optional[Dict[str, Any]]: Document data or None if not found
    """
    try:
        # Search for files with the document ID
        for file_path in settings.PROCESSED_FOLDER.glob(f"{document_id}_*.json"):
            with open(file_path, 'r', encoding='utf-8') as f:
                document = json.load(f)
                return document
        
        logger.warning(f"Document not found: {document_id}")
        return None
        
    except Exception as e:
        logger.error(f"Failed to retrieve document {document_id}: {e}")
        return None


def list_documents(
    user_id: Optional[str] = None,
    category: Optional[str] = None,
    limit: int = 50,
    offset: int = 0
) -> List[Dict[str, Any]]:
    """
    List processed documents with optional filtering.
    
    Args:
        user_id: Filter by user ID
        category: Filter by document category
        limit: Maximum number of documents to return
        offset: Number of documents to skip
        
    Returns:
        List[Dict[str, Any]]: List of document summaries
    """
    try:
        documents = []
        
        # Get all processed document files
        json_files = list(settings.PROCESSED_FOLDER.glob("*.json"))
        json_files.sort(key=lambda x: x.stat().st_mtime, reverse=True)  # Most recent first
        
        for file_path in json_files[offset:]:
            if len(documents) >= limit:
                break
                
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    document = json.load(f)
                
                # Apply filters
                if user_id and document.get("user_id") != user_id:
                    continue
                
                if category and document.get("classification", {}).get("category") != category:
                    continue
                
                # Create summary (exclude large fields)
                summary = {
                    "document_id": document.get("document_id"),
                    "file_name": document.get("file_name"),
                    "file_size": document.get("file_size"),
                    "user_id": document.get("user_id"),
                    "processing_timestamp": document.get("processing_timestamp"),
                    "status": document.get("status"),
                    "text_length": document.get("text_length", 0),
                    "entity_count": document.get("entity_count", 0),
                    "classification": document.get("classification", {}),
                    "summary": document.get("summary", "")[:200] + "..." if len(document.get("summary", "")) > 200 else document.get("summary", "")
                }
                
                documents.append(summary)
                
            except Exception as e:
                logger.warning(f"Failed to read document file {file_path}: {e}")
                continue
        
        return documents
        
    except Exception as e:
        logger.error(f"Failed to list documents: {e}")
        return []


def delete_document(document_id: str) -> bool:
    """
    Delete a processed document.
    
    Args:
        document_id: Unique document identifier
        
    Returns:
        bool: True if deleted successfully
    """
    try:
        # Find and delete document file
        for file_path in settings.PROCESSED_FOLDER.glob(f"{document_id}_*.json"):
            file_path.unlink()
            logger.info(f"Deleted document: {document_id}")
            return True
        
        logger.warning(f"Document not found for deletion: {document_id}")
        return False
        
    except Exception as e:
        logger.error(f"Failed to delete document {document_id}: {e}")
        return False


def get_processing_statistics() -> Dict[str, Any]:
    """
    Get statistics about document processing.
    
    Returns:
        Dict[str, Any]: Processing statistics
    """
    try:
        json_files = list(settings.PROCESSED_FOLDER.glob("*.json"))
        
        if not json_files:
            return {
                "total_documents": 0,
                "total_size_mb": 0,
                "categories": {},
                "processing_times": {}
            }
        
        stats = {
            "total_documents": len(json_files),
            "total_size_mb": 0,
            "categories": {},
            "processing_times": [],
            "status_counts": {},
            "average_text_length": 0
        }
        
        total_text_length = 0
        
        for file_path in json_files:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    document = json.load(f)
                
                # File size
                stats["total_size_mb"] += document.get("file_size", 0)
                
                # Category distribution
                category = document.get("classification", {}).get("category", "unknown")
                stats["categories"][category] = stats["categories"].get(category, 0) + 1
                
                # Processing times
                proc_time = document.get("processing_time_seconds", 0)
                if proc_time > 0:
                    stats["processing_times"].append(proc_time)
                
                # Status counts
                status = document.get("status", "unknown")
                stats["status_counts"][status] = stats["status_counts"].get(status, 0) + 1
                
                # Text length
                text_length = document.get("text_length", 0)
                total_text_length += text_length
                
            except Exception as e:
                logger.warning(f"Failed to read document stats from {file_path}: {e}")
                continue
        
        # Convert bytes to MB
        stats["total_size_mb"] = round(stats["total_size_mb"] / (1024 * 1024), 2)
        
        # Calculate averages
        if stats["processing_times"]:
            import statistics
            stats["average_processing_time"] = round(statistics.mean(stats["processing_times"]), 2)
            stats["median_processing_time"] = round(statistics.median(stats["processing_times"]), 2)
        
        stats["average_text_length"] = round(total_text_length / len(json_files))
        
        return stats
        
    except Exception as e:
        logger.error(f"Failed to calculate processing statistics: {e}")
        return {"error": str(e)}


def validate_file(file_path: str) -> Dict[str, Any]:
    """
    Validate a file before processing.
    
    Args:
        file_path: Path to file to validate
        
    Returns:
        Dict[str, Any]: Validation results
    """
    try:
        file_path = Path(file_path)
        
        validation = {
            "is_valid": False,
            "file_exists": file_path.exists(),
            "file_size": 0,
            "file_extension": "",
            "errors": []
        }
        
        if not file_path.exists():
            validation["errors"].append("File does not exist")
            return validation
        
        # Check file size
        file_size = file_path.stat().st_size
        validation["file_size"] = file_size
        
        if file_size > settings.MAX_FILE_SIZE:
            validation["errors"].append(f"File too large: {file_size} bytes (max: {settings.MAX_FILE_SIZE})")
        
        if file_size == 0:
            validation["errors"].append("File is empty")
        
        # Check file extension
        file_extension = file_path.suffix.lower()
        validation["file_extension"] = file_extension
        
        if file_extension not in settings.ALLOWED_EXTENSIONS:
            validation["errors"].append(f"Unsupported file type: {file_extension}")
        
        # If no errors, file is valid
        validation["is_valid"] = len(validation["errors"]) == 0
        
        return validation
        
    except Exception as e:
        return {
            "is_valid": False,
            "errors": [f"Validation failed: {str(e)}"]
        }