"""
Main FastAPI application entry point.

This module initializes the FastAPI app, sets up middleware, 
exception handlers, and includes all route modules.
"""

from fastapi import FastAPI, HTTPException, Request # type: ignore
from fastapi.middleware.cors import CORSMiddleware # type: ignore
from fastapi.staticfiles import StaticFiles # type: ignore
from fastapi.responses import JSONResponse # type: ignore
import logging
from pathlib import Path

from app.config import settings
from app.routes import upload, summarize, ner, search, classify, documents, chat, gemini_chat
from app.utils.logger import setup_logging

# Setup logging
setup_logging()
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="AI-powered document processing and intelligence platform",
    debug=settings.DEBUG
)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

# Global exception handler
@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """Global HTTP exception handler."""
    logger.error(f"HTTP {exc.status_code}: {exc.detail}")
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail, "status_code": exc.status_code}
    )

@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Global exception handler for unhandled exceptions."""
    logger.error(f"Unhandled exception: {str(exc)}")
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error", "status_code": 500}
    )

# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "app": settings.APP_NAME, "version": settings.APP_VERSION}

# Include routers
app.include_router(upload.router, prefix=settings.API_V1_PREFIX, tags=["upload"])
app.include_router(summarize.router, prefix=settings.API_V1_PREFIX, tags=["summarization"])
app.include_router(ner.router, prefix=settings.API_V1_PREFIX, tags=["ner"])
app.include_router(search.router, prefix=settings.API_V1_PREFIX, tags=["search"])
app.include_router(classify.router, prefix=settings.API_V1_PREFIX, tags=["classification"])
app.include_router(documents.router, prefix=settings.API_V1_PREFIX, tags=["documents"])
app.include_router(chat.router, prefix=settings.API_V1_PREFIX, tags=["gemini-ai"])
app.include_router(gemini_chat.router, prefix=settings.API_V1_PREFIX, tags=["gemini-advanced"])

# Serve static files (optional - for serving frontend if needed)
frontend_path = Path(__file__).parent.parent / "frontend" / "build"
if frontend_path.exists():
    app.mount("/static", StaticFiles(directory=str(frontend_path)), name="static")

@app.on_event("startup")
async def startup_event():
    """Application startup event."""
    logger.info(f"Starting {settings.APP_NAME} v{settings.APP_VERSION}")
    
    # Initialize search index on startup
    try:
        from app.services.search_service import build_index
        await build_index()
        logger.info("Search index initialized successfully")
    except Exception as e:
        logger.warning(f"Failed to initialize search index: {e}")

@app.on_event("shutdown")
async def shutdown_event():
    """Application shutdown event."""
    logger.info(f"Shutting down {settings.APP_NAME}")

if __name__ == "__main__":
    import uvicorn # type: ignore
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.DEBUG
    )