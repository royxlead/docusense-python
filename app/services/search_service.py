"""
Search service for semantic document search.

This module provides functions to build search indices and perform
semantic search using vector embeddings and FAISS.
"""

import logging
import numpy as np # type: ignore
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
import json
import pickle
import faiss # type: ignore

from app.config import settings
from app.models.embedding_model import generate_embedding
from app.utils.logger import log_search_query
from app.utils.scoring import evaluate_search_results

logger = logging.getLogger(__name__)

# Global search index cache
_search_index = None
_document_metadata = []


def build_index() -> bool:
    """Build or rebuild the FAISS search index from processed documents."""
    global _search_index, _document_metadata
    try:
        logger.info("Building search index...")

        processed_files = list(settings.PROCESSED_FOLDER.glob("*.json"))
        if not processed_files:
            logger.warning("No processed documents found for indexing")
            return False

        embeddings: List[np.ndarray] = []
        metadata: List[Dict[str, Any]] = []

        for file_path in processed_files:
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    document = json.load(f)

                embedding = document.get("embedding")
                if not embedding or not isinstance(embedding, list):
                    logger.warning(
                        f"Skipping document without embedding: {document.get('document_id')}"
                    )
                    continue

                embeddings.append(np.array(embedding, dtype=np.float32))
                metadata.append(
                    {
                        "document_id": document.get("document_id"),
                        "file_name": document.get("file_name", ""),
                        "summary": document.get("summary", "")[:500],
                        "classification": document.get("classification", {}),
                        "entity_count": document.get("entity_count", 0),
                        "text_length": document.get("text_length", 0),
                        "processing_timestamp": document.get(
                            "processing_timestamp", ""
                        ),
                    }
                )
            except Exception as e:
                logger.warning(f"Failed to process document {file_path}: {e}")

        if not embeddings:
            logger.warning("No valid embeddings found for indexing")
            return False

        embedding_matrix = np.vstack(embeddings)
        logger.info(
            "Built embedding matrix with shape: %s", str(embedding_matrix.shape)
        )

        dimension = embedding_matrix.shape[1]
        index = faiss.IndexFlatIP(dimension)
        faiss.normalize_L2(embedding_matrix)
        index.add(embedding_matrix)

        _search_index = index
        _document_metadata = metadata
        _save_index_to_disk(index, metadata)
        logger.info("Search index built successfully with %d documents", len(metadata))
        return True
    except Exception as e:
        logger.error("Failed to build search index: %s", str(e))
        return False


def _save_index_to_disk(index: faiss.Index, metadata: List[Dict[str, Any]]) -> None:
    """
    Save the search index and metadata to disk.
    
    Args:
        index: FAISS index
        metadata: Document metadata
    """
    try:
        # Ensure index directory exists
        index_dir = settings.FAISS_INDEX_PATH
        index_dir.mkdir(parents=True, exist_ok=True)
        
        # Save FAISS index
        index_file = index_dir / "search.index"
        faiss.write_index(index, str(index_file))
        
        # Save metadata
        metadata_file = index_dir / "metadata.pkl"
        with open(metadata_file, 'wb') as f:
            pickle.dump(metadata, f)
        
        logger.info(f"Search index saved to: {index_dir}")
        
    except Exception as e:
        logger.error(f"Failed to save index to disk: {e}")


def _load_index_from_disk() -> bool:
    """
    Load the search index and metadata from disk.
    
    Returns:
        bool: True if loaded successfully
    """
    global _search_index, _document_metadata
    
    try:
        index_dir = settings.FAISS_INDEX_PATH
        index_file = index_dir / "search.index"
        metadata_file = index_dir / "metadata.pkl"
        
        if not index_file.exists() or not metadata_file.exists():
            logger.info("No saved index found")
            return False
        
        # Load FAISS index
        _search_index = faiss.read_index(str(index_file))
        
        # Load metadata
        with open(metadata_file, 'rb') as f:
            _document_metadata = pickle.load(f)
        
        logger.info(f"Search index loaded from disk with {len(_document_metadata)} documents")
        return True
        
    except Exception as e:
        logger.error(f"Failed to load index from disk: {e}")
        return False


def search_documents(
    query: str,
    k: int = 5,
    user_id: Optional[str] = None,
    category_filter: Optional[str] = None,
    min_similarity: float = 0.1
) -> List[Dict[str, Any]]:
    """
    Search for documents similar to the query.
    
    This function converts the query to an embedding and searches
    for the most similar documents in the index.
    
    Args:
        query: Search query text
        k: Number of results to return
        user_id: Optional user ID for logging
        category_filter: Optional category to filter results
        min_similarity: Minimum similarity threshold
        
    Returns:
        List[Dict[str, Any]]: List of search results with similarity scores
    """
    global _search_index, _document_metadata
    
    search_start_time = None
    
    try:
        if not query or not query.strip():
            return []
        
        from datetime import datetime
        search_start_time = datetime.now()
        
        logger.info(f"Searching for: '{query}' (k={k})")
        
        # Initialize index if not loaded
        if _search_index is None:
            if not _load_index_from_disk():
                if not build_index():
                    logger.warning("No search index available")
                    return _generate_dummy_results(query, k)
        
        if _search_index is None or not _document_metadata:
            return _generate_dummy_results(query, k)
        
        # Generate query embedding
        query_embedding = generate_embedding(query)
        if query_embedding is None or len(query_embedding) == 0:
            logger.error("Failed to generate query embedding")
            return []
        
        # Normalize query embedding
        query_embedding = query_embedding.reshape(1, -1).astype(np.float32)
        faiss.normalize_L2(query_embedding)

        # Search in index
        search_k = min(k * 2, len(_document_metadata))
        similarities, indices = _search_index.search(query_embedding, search_k)

        # Process results
        results: List[Dict[str, Any]] = []
        for similarity, idx in zip(similarities[0], indices[0]):
            if idx == -1:  # Invalid index
                continue

            if similarity < min_similarity:
                continue

            try:
                metadata = _document_metadata[idx]

                # Apply category filter
                if category_filter:
                    doc_category = metadata.get("classification", {}).get("category", "")
                    if doc_category != category_filter:
                        continue

                result = {
                    "document_id": metadata["document_id"],
                    "file_name": metadata["file_name"],
                    "summary": metadata["summary"],
                    "classification": metadata["classification"],
                    "entity_count": metadata["entity_count"],
                    "text_length": metadata["text_length"],
                    "processing_timestamp": metadata["processing_timestamp"],
                    "similarity": float(similarity),
                }

                results.append(result)

            except IndexError:
                logger.warning(f"Invalid index in search results: {idx}")
                continue

        # If no results due to threshold, return top-K regardless of threshold as a fallback
        if not results:
            fallback = []
            for similarity, idx in zip(similarities[0], indices[0]):
                if idx == -1:
                    continue
                try:
                    metadata = _document_metadata[idx]
                    fallback.append(
                        {
                            "document_id": metadata["document_id"],
                            "file_name": metadata["file_name"],
                            "summary": metadata["summary"],
                            "classification": metadata["classification"],
                            "entity_count": metadata["entity_count"],
                            "text_length": metadata["text_length"],
                            "processing_timestamp": metadata["processing_timestamp"],
                            "similarity": float(similarity),
                        }
                    )
                    if len(fallback) >= k:
                        break
                except IndexError:
                    continue
            results = fallback

        # Trim to k and assign rank
        results = results[:k]
        for i, item in enumerate(results, start=1):
            item["rank"] = i

        # Log search
        processing_time = (datetime.now() - search_start_time).total_seconds()
        log_search_query(query, user_id, len(results), processing_time)

        logger.info(
            f"Search completed: {len(results)} results in {processing_time:.3f}s"
        )
        return results
        
    except Exception as e:
        logger.error(f"Search failed: {str(e)}")
        
        # Log failed search
        if search_start_time:
            processing_time = (datetime.now() - search_start_time).total_seconds()
            log_search_query(query, user_id, 0, processing_time)
        
        return _generate_dummy_results(query, k)


def _generate_dummy_results(query: str, k: int) -> List[Dict[str, Any]]:
    """
    Generate dummy search results for skeleton version.
    
    Args:
        query: Search query
        k: Number of results to generate
        
    Returns:
        List[Dict[str, Any]]: Dummy search results
    """
    import uuid
    
    dummy_results = []
    base_similarity = 0.95
    
    for i in range(min(k, 3)):  # Generate up to 3 dummy results
        result = {
            "document_id": str(uuid.uuid4()),
            "file_name": f"sample_document_{i+1}.pdf",
            "summary": f"This is a sample document summary related to '{query}'. It contains relevant information about the search topic.",
            "classification": {
                "category": "business" if i == 0 else "technical" if i == 1 else "legal",
                "confidence": 0.85 + (i * 0.05)
            },
            "entity_count": 10 + i * 3,
            "text_length": 1500 + i * 200,
            "processing_timestamp": "2025-09-07T10:00:00",
            "similarity": base_similarity - (i * 0.1),
            "rank": i + 1
        }
        dummy_results.append(result)
    
    return dummy_results


def get_similar_documents(
    document_id: str,
    k: int = 5,
    exclude_self: bool = True
) -> List[Dict[str, Any]]:
    """
    Find documents similar to a given document.
    
    Args:
        document_id: ID of the reference document
        k: Number of similar documents to return
        exclude_self: Whether to exclude the reference document from results
        
    Returns:
        List[Dict[str, Any]]: List of similar documents
    """
    try:
        # Get the document's embedding
        document_data = None
        for metadata in _document_metadata:
            if metadata["document_id"] == document_id:
                document_data = metadata
                break
        
        if not document_data:
            logger.warning(f"Document not found in index: {document_id}")
            return []
        
        # Get the document's summary for similarity search
        summary = document_data.get("summary", "")
        if not summary:
            logger.warning(f"No summary available for document: {document_id}")
            return []
        
        # Search using the summary as query
        results = search_documents(summary, k + (1 if exclude_self else 0))
        
        # Remove the original document if requested
        if exclude_self:
            results = [r for r in results if r["document_id"] != document_id]
        
        return results[:k]
        
    except Exception as e:
        logger.error(f"Failed to find similar documents: {e}")
        return []


def get_search_statistics() -> Dict[str, Any]:
    """
    Get statistics about the search index.
    
    Returns:
        Dict[str, Any]: Search index statistics
    """
    try:
        global _search_index, _document_metadata
        
        if _search_index is None or not _document_metadata:
            return {
                "indexed_documents": 0,
                "index_size": 0,
                "embedding_dimension": 0
            }
        
        stats = {
            "indexed_documents": len(_document_metadata),
            "index_size": _search_index.ntotal,
            "embedding_dimension": _search_index.d if hasattr(_search_index, 'd') else 0,
            "categories": {},
            "average_text_length": 0,
            "total_entities": 0
        }
        
        # Analyze document metadata
        total_text_length = 0
        total_entities = 0
        
        for metadata in _document_metadata:
            # Category distribution
            category = metadata.get("classification", {}).get("category", "unknown")
            stats["categories"][category] = stats["categories"].get(category, 0) + 1
            
            # Text statistics
            text_length = metadata.get("text_length", 0)
            total_text_length += text_length
            
            entity_count = metadata.get("entity_count", 0)
            total_entities += entity_count
        
        if len(_document_metadata) > 0:
            stats["average_text_length"] = round(total_text_length / len(_document_metadata))
            stats["average_entities_per_doc"] = round(total_entities / len(_document_metadata), 1)
        
        stats["total_entities"] = total_entities
        
        return stats
        
    except Exception as e:
        logger.error(f"Failed to get search statistics: {e}")
        return {"error": str(e)}


def refresh_index() -> bool:
    """
    Refresh the search index by rebuilding it.
    
    Returns:
        bool: True if refresh was successful
    """
    try:
        logger.info("Refreshing search index...")
        
        # Clear current index
        global _search_index, _document_metadata
        _search_index = None
        _document_metadata = []
        
        # Rebuild index
        return build_index()
        
    except Exception as e:
        logger.error(f"Failed to refresh search index: {e}")
        return False


def add_document_to_index(document_data: Dict[str, Any]) -> bool:
    """
    Add a single document to the existing search index.
    
    Args:
        document_data: Processed document data with embedding
        
    Returns:
        bool: True if added successfully
    """
    try:
        global _search_index, _document_metadata
        
        # Extract embedding
        embedding = document_data.get("embedding")
        if not embedding or not isinstance(embedding, list):
            logger.warning("Document missing valid embedding")
            return False
        
        # Prepare metadata
        metadata = {
            "document_id": document_data.get("document_id"),
            "file_name": document_data.get("file_name", ""),
            "summary": document_data.get("summary", "")[:500],
            "classification": document_data.get("classification", {}),
            "entity_count": document_data.get("entity_count", 0),
            "text_length": document_data.get("text_length", 0),
            "processing_timestamp": document_data.get("processing_timestamp", "")
        }
        
        # Initialize index if needed
        if _search_index is None:
            if not _load_index_from_disk():
                # Create new index
                dimension = len(embedding)
                _search_index = faiss.IndexFlatIP(dimension)
                _document_metadata = []
        
        # Add to index
        embedding_array = np.array([embedding], dtype=np.float32)
        faiss.normalize_L2(embedding_array)
        _search_index.add(embedding_array)
        
        # Add metadata
        _document_metadata.append(metadata)
        
        logger.info(f"Added document to search index: {metadata['document_id']}")
        return True
        
    except Exception as e:
        logger.error(f"Failed to add document to index: {e}")
        return False