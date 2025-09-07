"""
File upload API routes.

This module provides endpoints for uploading and processing documents
through the document intelligence pipeline.
"""

import logging
import os
import shutil
from datetime import datetime
from pathlib import Path
from typing import Optional
from fastapi import APIRouter, File, UploadFile, HTTPException, BackgroundTasks, Depends
from fastapi.responses import JSONResponse
import aiofiles

from app.config import settings
from app.services.document_service import process_document, validate_file
from app.utils.logger import log_api_call

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/upload")
async def upload_file(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...)
):
    """
    Upload and process a document file.
    
    This endpoint accepts a file upload, saves it to the upload directory,
    and initiates processing through the document intelligence pipeline.
    
    Args:
        background_tasks: FastAPI background tasks
        file: Uploaded file
        
    Returns:
        JSONResponse: Upload and processing results
    """
    start_time = datetime.now()
    user_id = "anonymous"  # For now, allow anonymous uploads
    
    try:
        logger.info(f"File upload initiated: {file.filename}")
        
        # Validate file
        if not file.filename:
            raise HTTPException(status_code=400, detail="No file provided")
        
        # Check file extension
        file_extension = Path(file.filename).suffix.lower()
        if file_extension not in settings.ALLOWED_EXTENSIONS:
            raise HTTPException(
                status_code=400,
                detail=f"Unsupported file type: {file_extension}. Allowed: {list(settings.ALLOWED_EXTENSIONS)}"
            )
        
        # Check file size
        file_size = 0
        if hasattr(file.file, 'seek'):
            file.file.seek(0, 2)  # Seek to end
            file_size = file.file.tell()
            file.file.seek(0)  # Reset to beginning
        
        if file_size > settings.MAX_FILE_SIZE:
            raise HTTPException(
                status_code=400,
                detail=f"File too large: {file_size} bytes (max: {settings.MAX_FILE_SIZE})"
            )
        
        # Generate unique filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        safe_filename = f"{timestamp}_{file.filename}"
        file_path = settings.UPLOAD_FOLDER / safe_filename
        
        # Save uploaded file
        try:
            async with aiofiles.open(file_path, 'wb') as f:
                content = await file.read()
                await f.write(content)
            
            logger.info(f"File saved to: {file_path}")
        except Exception as e:
            logger.error(f"Failed to save file: {e}")
            raise HTTPException(status_code=500, detail="Failed to save uploaded file")
        
        # Validate saved file
        validation = validate_file(str(file_path))
        if not validation["is_valid"]:
            # Remove invalid file
            try:
                file_path.unlink()
            except Exception:
                pass
            raise HTTPException(
                status_code=400,
                detail=f"File validation failed: {validation['errors']}"
            )
        
        # Process document in background
        background_tasks.add_task(process_document, str(file_path), user_id)
        
        # Log API call
        processing_time = (datetime.now() - start_time).total_seconds()
        log_api_call(
            endpoint="/upload",
            method="POST",
            user_id=user_id,
            request_data={"filename": file.filename, "file_size": file_size},
            response_status=200,
            processing_time=processing_time
        )
        
        return JSONResponse(
            status_code=200,
            content={
                "message": "File uploaded successfully",
                "filename": file.filename,
                "file_path": str(file_path),
                "file_size": file_size,
                "processing_status": "initiated",
                "estimated_processing_time": "2-5 minutes",
                "processing_timestamp": datetime.now().isoformat()
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        processing_time = (datetime.now() - start_time).total_seconds()
        logger.error(f"Upload failed: {str(e)}")
        
        # Log failed API call
        log_api_call(
            endpoint="/upload",
            method="POST",
            user_id=user_id,
            response_status=500,
            processing_time=processing_time
        )
        
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")


@router.post("/upload-and-wait")
async def upload_and_wait(
    file: UploadFile = File(...)
):
    """
    Upload and process a document file synchronously.
    
    This endpoint uploads a file and waits for processing to complete
    before returning the full results.
    
    Args:
        file: Uploaded file
        
    Returns:
        JSONResponse: Complete processing results
    """
    start_time = datetime.now()
    user_id = "anonymous"  # For now, allow anonymous uploads
    
    try:
        logger.info(f"Synchronous file upload initiated: {file.filename}")
        
        # Validate file
        if not file.filename:
            raise HTTPException(status_code=400, detail="No file provided")
        
        file_extension = Path(file.filename).suffix.lower()
        if file_extension not in settings.ALLOWED_EXTENSIONS:
            raise HTTPException(
                status_code=400,
                detail=f"Unsupported file type: {file_extension}"
            )
        
        # Generate unique filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        safe_filename = f"{timestamp}_{file.filename}"
        file_path = settings.UPLOAD_FOLDER / safe_filename
        
        # Save uploaded file
        async with aiofiles.open(file_path, 'wb') as f:
            content = await file.read()
            await f.write(content)
        
        # Validate saved file
        validation = validate_file(str(file_path))
        if not validation["is_valid"]:
            file_path.unlink()
            raise HTTPException(
                status_code=400,
                detail=f"File validation failed: {validation['errors']}"
            )
        
        # Process document synchronously
        processing_result = process_document(str(file_path), user_id)
        
        # Log API call
        processing_time = (datetime.now() - start_time).total_seconds()
        log_api_call(
            endpoint="/upload-and-wait",
            method="POST",
            user_id=user_id,
            request_data={"filename": file.filename},
            response_status=200,
            processing_time=processing_time
        )
        
        return JSONResponse(
            status_code=200,
            content={
                "message": "File uploaded and processed successfully",
                "processing_result": processing_result
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        processing_time = (datetime.now() - start_time).total_seconds()
        logger.error(f"Synchronous upload failed: {str(e)}")
        
        log_api_call(
            endpoint="/upload-and-wait",
            method="POST",
            user_id=user_id,
            response_status=500,
            processing_time=processing_time
        )
        
        raise HTTPException(status_code=500, detail=f"Upload and processing failed: {str(e)}")


@router.get("/upload-status/{filename}")
async def get_upload_status(
    filename: str
):
    """
    Check the processing status of an uploaded file.
    
    Args:
        filename: Name of the uploaded file
        
    Returns:
        JSONResponse: Processing status information
    """
    try:
        # Search for files matching the pattern
        upload_files = list(settings.UPLOAD_FOLDER.glob(f"*_{filename}"))
        processed_files = list(settings.PROCESSED_FOLDER.glob("*.json"))
        
        if not upload_files:
            raise HTTPException(status_code=404, detail="File not found")
        
        file_path = upload_files[0]  # Take the first match
        
        # Check if processing is complete
        for processed_file in processed_files:
            try:
                import json
                with open(processed_file, 'r') as f:
                    data = json.load(f)
                
                if data.get("file_name") == filename:
                    return JSONResponse(
                        content={
                            "filename": filename,
                            "status": "completed",
                            "document_id": data.get("document_id"),
                            "processing_result": data
                        }
                    )
            except Exception:
                continue
        
        # File uploaded but not yet processed
        return JSONResponse(
            content={
                "filename": filename,
                "status": "processing",
                "message": "File is still being processed"
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Status check failed: {str(e)}")
        raise HTTPException(status_code=500, detail="Status check failed")


@router.delete("/upload/{filename}")
async def delete_uploaded_file(
    filename: str
):
    """
    Delete an uploaded file.
    
    Args:
        filename: Name of the file to delete
        
    Returns:
        JSONResponse: Deletion confirmation
    """
    try:
        # For now, allow anyone to delete files (in production, add proper auth)
        
        # Find and delete the file
        upload_files = list(settings.UPLOAD_FOLDER.glob(f"*_{filename}"))
        
        if not upload_files:
            raise HTTPException(status_code=404, detail="File not found")
        
        deleted_count = 0
        for file_path in upload_files:
            try:
                file_path.unlink()
                deleted_count += 1
                logger.info(f"Deleted uploaded file: {file_path}")
            except Exception as e:
                logger.warning(f"Failed to delete file {file_path}: {e}")
        
        if deleted_count == 0:
            raise HTTPException(status_code=500, detail="Failed to delete file")
        
        return JSONResponse(
            content={
                "message": f"Successfully deleted {deleted_count} file(s)",
                "filename": filename
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"File deletion failed: {str(e)}")
        raise HTTPException(status_code=500, detail="File deletion failed")


@router.get("/uploads")
async def list_uploads():
    """
    List all uploaded files.
    
    Returns:
        JSONResponse: List of uploaded files
    """
    try:
        upload_files = list(settings.UPLOAD_FOLDER.glob("*"))
        
        files_info = []
        for file_path in upload_files:
            if file_path.is_file():
                stat = file_path.stat()
                files_info.append({
                    "filename": file_path.name,
                    "size": stat.st_size,
                    "uploaded_at": datetime.fromtimestamp(stat.st_ctime).isoformat(),
                    "modified_at": datetime.fromtimestamp(stat.st_mtime).isoformat()
                })
        
        # Sort by upload time (newest first)
        files_info.sort(key=lambda x: x["uploaded_at"], reverse=True)
        
        return JSONResponse(
            content={
                "files": files_info,
                "total_files": len(files_info),
                "total_size": sum(f["size"] for f in files_info)
            }
        )
        
    except Exception as e:
        logger.error(f"Failed to list uploads: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to list uploads")