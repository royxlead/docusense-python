"""
Gemini-powered document chat and advanced analysis routes.
"""

import logging
from typing import Dict, Any
from fastapi import APIRouter, HTTPException # type: ignore
from fastapi.responses import JSONResponse # type: ignore
from pydantic import BaseModel # type: ignore

from app.services.gemini_service import gemini_service
from app.services.document_service import get_document_by_id

logger = logging.getLogger(__name__)
router = APIRouter()


class ChatRequest(BaseModel):
    document_id: str
    question: str


class AnalysisRequest(BaseModel):
    document_id: str
    analysis_type: str = "insights"  # insights, report, classification


class SummarizationRequest(BaseModel):
    document_id: str
    style: str = "professional"  # professional, executive, technical, casual


@router.post("/chat")
async def chat_with_document(request: ChatRequest):
    """
    Chat with a document using Gemini AI.
    
    Ask natural language questions about any processed document.
    """
    try:
        # Get document data
        document_data = get_document_by_id(request.document_id)
        if not document_data:
            raise HTTPException(status_code=404, detail="Document not found")

        if not gemini_service.is_available():
            raise HTTPException(status_code=503, detail="Gemini AI service not available")

        # Get answer from Gemini
        answer = await gemini_service.document_qa(
            document_data.get("raw_text") or document_data.get("text", ""),
            request.question,
        )

        return JSONResponse(
            {
                "document_id": request.document_id,
                "question": request.question,
                "answer": answer,
                "document_name": document_data.get("file_name", "Unknown"),
            }
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Document chat failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/enhanced-summary")
async def get_enhanced_summary(request: SummarizationRequest):
    """
    Get enhanced summary using Gemini AI.
    
    Provides more sophisticated summarization with different styles.
    """
    try:
        # Get document data
        document_data = get_document_by_id(request.document_id)
        if not document_data:
            raise HTTPException(status_code=404, detail="Document not found")

        if not gemini_service.is_available():
            # Fallback to original summary
            return JSONResponse(
                {
                    "document_id": request.document_id,
                    "style": request.style,
                    "summary": document_data.get("summary", "No summary available"),
                    "enhanced": False,
                    "note": "Using original summary - Gemini not available",
                }
            )

        # Get enhanced summary from Gemini
        enhanced_summary = await gemini_service.enhanced_summarization(
            document_data.get("raw_text") or document_data.get("text", ""),
            request.style,
        )

        return JSONResponse(
            {
                "document_id": request.document_id,
                "style": request.style,
                "summary": enhanced_summary,
                "original_summary": document_data.get("summary", ""),
                "enhanced": True,
            }
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Enhanced summarization failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/advanced-analysis")
async def get_advanced_analysis(request: AnalysisRequest):
    """
    Get advanced document analysis using Gemini AI.
    
    Provides deeper insights, comprehensive reports, or advanced classification.
    """
    try:
        # Get document data
        document_data = get_document_by_id(request.document_id)
        if not document_data:
            raise HTTPException(status_code=404, detail="Document not found")

        if not gemini_service.is_available():
            raise HTTPException(status_code=503, detail="Gemini AI service not available")

        if request.analysis_type == "insights":
            # Extract deeper insights
            insights = await gemini_service.extract_insights(
                document_data.get("raw_text") or document_data.get("text", "")
            )
            return JSONResponse(
                {
                    "document_id": request.document_id,
                    "analysis_type": "insights",
                    "results": insights,
                }
            )

        elif request.analysis_type == "report":
            # Generate comprehensive report
            report = await gemini_service.generate_report(document_data)
            return JSONResponse(
                {
                    "document_id": request.document_id,
                    "analysis_type": "report",
                    "report": report,
                    "generated_at": "2025-09-07T10:00:00",
                }
            )

        elif request.analysis_type == "classification":
            # Advanced classification
            classification = await gemini_service.advanced_classification(
                document_data.get("raw_text") or document_data.get("text", "")
            )
            return JSONResponse(
                {
                    "document_id": request.document_id,
                    "analysis_type": "classification",
                    "advanced_classification": classification,
                    "original_classification": document_data.get(
                        "classification", {}
                    ),
                }
            )

        else:
            raise HTTPException(status_code=400, detail="Invalid analysis type")

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Advanced analysis failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/chat-suggestions/{document_id}")
async def get_chat_suggestions(document_id: str):
    """
    Get suggested questions for document chat.
    
    Provides intelligent question suggestions based on document content.
    """
    try:
        # Get document data
        document_data = get_document_by_id(document_id)
        if not document_data:
            raise HTTPException(status_code=404, detail="Document not found")

        # Generate context-aware suggestions
        doc_type = document_data.get("classification", {}).get("category", "unknown")

        suggestions = {
            "business": [
                "What are the key business objectives mentioned?",
                "What are the main financial implications?",
                "Who are the key stakeholders involved?",
                "What are the proposed timelines?",
                "What risks are identified?",
            ],
            "legal": [
                "What are the main legal obligations?",
                "Who are the parties involved?",
                "What are the key terms and conditions?",
                "What are the penalties or consequences?",
                "When do the obligations take effect?",
            ],
            "technical": [
                "What are the technical requirements?",
                "What technologies are mentioned?",
                "What are the implementation steps?",
                "What are the system dependencies?",
                "What are the performance specifications?",
            ],
            "medical": [
                "What is the main diagnosis or condition?",
                "What treatments are recommended?",
                "What are the patient's symptoms?",
                "What medications are prescribed?",
                "What follow-up actions are needed?",
            ],
            "financial": [
                "What are the key financial figures?",
                "What is the budget or cost breakdown?",
                "What are the revenue projections?",
                "What expenses are identified?",
                "What is the ROI or profitability analysis?",
            ],
        }

        return JSONResponse(
            {
                "document_id": document_id,
                "document_type": doc_type,
                "suggestions": suggestions.get(
                    doc_type,
                    [
                        "What is the main purpose of this document?",
                        "What are the key points mentioned?",
                        "Who are the people or organizations involved?",
                        "What actions are recommended?",
                        "What are the important dates or deadlines?",
                    ],
                ),
            }
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Chat suggestions failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))
