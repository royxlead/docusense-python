"""
Document Chat API using Gemini AI.
Allows users to ask questions about their uploaded documents.
"""

import logging
import json
from typing import Dict, Any
from fastapi import APIRouter, HTTPException # type: ignore
from fastapi.responses import JSONResponse # pyright: ignore[reportMissingImports]
from pydantic import BaseModel # type: ignore

import google.generativeai as genai # type: ignore
from app.config import settings

logger = logging.getLogger(__name__)
router = APIRouter()

class ChatRequest(BaseModel):
    document_id: str
    question: str
    conversation_history: list = []

@router.post("/documents/{document_id}/chat")
async def chat_with_document(document_id: str, request: ChatRequest):
    """
    Chat with a specific document using Gemini AI.
    
    Args:
        document_id: ID of the document to chat about
        request: Chat request containing question and history
        
    Returns:
        JSON response with AI answer
    """
    try:
        # Load the document data
        processed_files = list(settings.PROCESSED_FOLDER.glob("*.json"))
        document_data = None
        
        for file_path in processed_files:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    doc_data = json.load(f)
                    if doc_data.get("document_id") == document_id:
                        document_data = doc_data
                        break
            except Exception as e:
                logger.error(f"Error reading document {file_path}: {e}")
                continue
        
        if not document_data:
            raise HTTPException(status_code=404, detail="Document not found")
        
        # Generate response using Gemini
        response = await _generate_chat_response(
            document_data, 
            request.question, 
            request.conversation_history
        )
        
        from datetime import datetime
        return JSONResponse({
            "document_id": document_id,
            "question": request.question,
            "answer": response,
            "timestamp": datetime.now().isoformat()
        })
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Chat failed for document {document_id}: {e}")
        raise HTTPException(status_code=500, detail="Chat service unavailable")

async def _generate_chat_response(
    document_data: Dict[str, Any], 
    question: str, 
    history: list
) -> str:
    """
    Generate a chat response using Gemini AI.
    """
    try:
        if not settings.GEMINI_API_KEY:
            raise Exception("Gemini API key not configured")
        
        genai.configure(api_key=settings.GEMINI_API_KEY)
        model = genai.GenerativeModel(settings.GEMINI_MODEL)
        
        # Build context from document
        document_context = f"""
Document: {document_data.get('file_name', 'Unknown')}
Category: {document_data.get('classification', {}).get('category', 'Unknown')}
Summary: {document_data.get('summary', 'No summary available')}

Key Entities:
"""
        
        # Add entities to context
        entities = document_data.get('entities', {})
        for entity_type, entity_list in entities.items():
            if entity_list:
                entities_text = ', '.join([str(e) if isinstance(e, str) else str(e.get('text', e)) for e in entity_list[:5]])
                document_context += f"- {entity_type}: {entities_text}\n"
        
        # Add document text (truncated)
        raw_text = document_data.get('raw_text') or document_data.get('text', '')
        if raw_text:
            document_context += f"\nDocument Content (excerpt):\n{raw_text[:2000]}..."
        
        # Build conversation history
        history_context = ""
        if history:
            history_context = "\nPrevious conversation:\n"
            for entry in history[-5:]:  # Last 5 exchanges
                history_context += f"Q: {entry.get('question', '')}\nA: {entry.get('answer', '')}\n"
        
        # Create the prompt
        prompt = f"""
You are a helpful AI assistant that answers questions about documents. 
Based on the document information provided below, please answer the user's question accurately and concisely.

{document_context}
{history_context}

User Question: {question}

Please provide a helpful answer based on the document content. If the information is not available in the document, please say so clearly.

Answer:"""
        
        # Generate response
        response = model.generate_content(prompt)
        
        if response and response.text:
            return response.text.strip()
        else:
            return "I apologize, but I couldn't generate a response. Please try rephrasing your question."
            
    except Exception as e:
        logger.error(f"Gemini chat generation failed: {e}")
        return f"I'm sorry, but I'm unable to answer your question about this document at the moment. Please try again later."

@router.get("/documents/{document_id}/summary")
async def get_enhanced_summary(document_id: str):
    """
    Get an enhanced summary of a document using Gemini AI.
    """
    try:
        # Load document
        processed_files = list(settings.PROCESSED_FOLDER.glob("*.json"))
        document_data = None
        
        for file_path in processed_files:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    doc_data = json.load(f)
                    if doc_data.get("document_id") == document_id:
                        document_data = doc_data
                        break
            except Exception as e:
                continue
        
        if not document_data:
            raise HTTPException(status_code=404, detail="Document not found")
        
        # Generate enhanced summary with Gemini
        enhanced_summary = await _generate_enhanced_summary(document_data)
        
        return JSONResponse({
            "document_id": document_id,
            "original_summary": document_data.get('summary', ''),
            "enhanced_summary": enhanced_summary,
            "insights": await _generate_document_insights(document_data)
        })
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Enhanced summary failed for {document_id}: {e}")
        raise HTTPException(status_code=500, detail="Summary service unavailable")

async def _generate_enhanced_summary(document_data: Dict[str, Any]) -> str:
    """Generate an enhanced summary using Gemini."""
    try:
        genai.configure(api_key=settings.GEMINI_API_KEY)
        model = genai.GenerativeModel(settings.GEMINI_MODEL)
        
        raw_text = document_data.get('raw_text') or document_data.get('text', '')
        if not raw_text:
            return "No content available for summary."
        
        prompt = f"""
Please create a comprehensive summary of this document:

{raw_text[:4000]}

The summary should include:
1. Main purpose/type of document
2. Key information and highlights
3. Important details (names, dates, numbers)
4. Conclusions or outcomes if applicable

Provide a well-structured summary in paragraph format:
"""
        
        response = model.generate_content(prompt)
        return response.text.strip() if response and response.text else "Summary unavailable."
        
    except Exception as e:
        logger.error(f"Enhanced summary generation failed: {e}")
        return "Enhanced summary currently unavailable."

async def _generate_document_insights(document_data: Dict[str, Any]) -> list:
    """Generate key insights about the document."""
    try:
        genai.configure(api_key=settings.GEMINI_API_KEY)
        model = genai.GenerativeModel(settings.GEMINI_MODEL)
        
        raw_text = document_data.get('raw_text') or document_data.get('text', '')
        if not raw_text:
            return []
        
        prompt = f"""
Analyze this document and provide 3-5 key insights or important points:

{raw_text[:3000]}

Format your response as a simple list of insights, one per line, starting with a dash (-).
Focus on the most important and actionable information.

Insights:
"""
        
        response = model.generate_content(prompt)
        if response and response.text:
            insights = []
            for line in response.text.strip().split('\n'):
                line = line.strip()
                if line.startswith('-') or line.startswith('•'):
                    insights.append(line[1:].strip())
                elif line and not line.startswith('Insights:'):
                    insights.append(line)
            return insights[:5]  # Max 5 insights
        
        return []
        
    except Exception as e:
        logger.error(f"Insights generation failed: {e}")
        return []
