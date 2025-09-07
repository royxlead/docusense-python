"""
Gemini AI service for enhanced document intelligence.

This module provides integration with Google's Gemini API for advanced
document analysis, summarization, and question-answering capabilities.
"""

import logging
import json
from typing import Dict, Any, List, Optional
import google.generativeai as genai # type: ignore
from app.config import settings

logger = logging.getLogger(__name__)

class GeminiService:
    """Service for Gemini AI integration."""
    
    def __init__(self):
        """Initialize Gemini service."""
        self.model = None
        self._initialize_gemini()
    
    def _initialize_gemini(self):
        """Initialize Gemini API connection."""
        try:
            if settings.GEMINI_API_KEY:
                genai.configure(api_key=settings.GEMINI_API_KEY)
                self.model = genai.GenerativeModel(settings.GEMINI_MODEL)
                logger.info(f"Gemini API initialized with model: {settings.GEMINI_MODEL}")
            else:
                logger.warning("Gemini API key not provided. Gemini features disabled.")
        except Exception as e:
            logger.error(f"Failed to initialize Gemini API: {e}")
            self.model = None
    
    def is_available(self) -> bool:
        """Check if Gemini service is available."""
        return self.model is not None
    
    async def enhanced_summarization(self, text: str, style: str = "professional") -> str:
        """
        Generate enhanced summary using Gemini.
        
        Args:
            text: Text to summarize
            style: Summary style (professional, executive, technical, casual)
            
        Returns:
            Enhanced summary
        """
        if not self.is_available():
            return "Gemini service not available"
        
        try:
            prompt = f"""
            Please provide a {style} summary of the following document. 
            Make it comprehensive yet concise, highlighting key points, insights, and actionable information.
            
            Document text:
            {text[:4000]}  # Limit input size
            
            Summary:
            """
            
            response = self.model.generate_content(
                prompt,
                generation_config=genai.types.GenerationConfig(
                    temperature=settings.GEMINI_TEMPERATURE,
                    max_output_tokens=settings.GEMINI_MAX_TOKENS
                )
            )
            
            return response.text if response.text else "Could not generate summary"
            
        except Exception as e:
            logger.error(f"Gemini summarization failed: {e}")
            return f"Summarization failed: {str(e)}"
    
    async def document_qa(self, document_text: str, question: str) -> str:
        """
        Answer questions about a document using Gemini.
        
        Args:
            document_text: Full document text
            question: User question
            
        Returns:
            Answer to the question
        """
        if not self.is_available():
            return "Gemini service not available"
        
        try:
            prompt = f"""
            Based on the following document, please answer the question accurately and comprehensively.
            If the answer is not in the document, please say so.
            
            Document:
            {document_text[:6000]}  # Limit input size
            
            Question: {question}
            
            Answer:
            """
            
            response = self.model.generate_content(
                prompt,
                generation_config=genai.types.GenerationConfig(
                    temperature=settings.GEMINI_TEMPERATURE,
                    max_output_tokens=1024
                )
            )
            
            return response.text if response.text else "Could not generate answer"
            
        except Exception as e:
            logger.error(f"Gemini Q&A failed: {e}")
            return f"Question answering failed: {str(e)}"
    
    async def advanced_classification(self, text: str) -> Dict[str, Any]:
        """
        Perform advanced document classification using Gemini.
        
        Args:
            text: Document text
            
        Returns:
            Classification results with confidence and reasoning
        """
        if not self.is_available():
            return {"category": "unknown", "confidence": 0.0, "reasoning": "Gemini not available"}
        
        try:
            prompt = f"""
            Analyze the following document and classify it into one of these categories:
            - business: Business documents, contracts, proposals, reports, strategic plans
            - legal: Legal documents, agreements, court filings, compliance documents
            - technical: Technical documentation, manuals, specifications, engineering reports
            - medical: Medical records, research papers, health documents, clinical reports
            - financial: Financial reports, invoices, statements, budgets, audit documents
            - academic: Research papers, theses, educational content, journal articles
            - administrative: Administrative documents, memos, policies, procedures, correspondence
            
            Please respond in JSON format with:
            - category: the classification category
            - confidence: confidence score (0.0-1.0)
            - reasoning: brief explanation for the classification
            - key_indicators: list of text elements that led to this classification
            
            Document text:
            {text[:3000]}
            
            Classification (JSON only):
            """
            
            response = self.model.generate_content(
                prompt,
                generation_config=genai.types.GenerationConfig(
                    temperature=0.1,  # Lower temperature for more consistent JSON
                    max_output_tokens=500
                )
            )
            
            # Try to parse JSON response
            try:
                result = json.loads(response.text)
                return result
            except json.JSONDecodeError:
                # Fallback if JSON parsing fails
                return {
                    "category": "unknown",
                    "confidence": 0.5,
                    "reasoning": "Could not parse classification result",
                    "raw_response": response.text
                }
            
        except Exception as e:
            logger.error(f"Gemini classification failed: {e}")
            return {
                "category": "unknown",
                "confidence": 0.0,
                "reasoning": f"Classification failed: {str(e)}"
            }
    
    async def extract_insights(self, text: str) -> Dict[str, Any]:
        """
        Extract deeper insights from document using Gemini.
        
        Args:
            text: Document text
            
        Returns:
            Insights including themes, sentiment, recommendations
        """
        if not self.is_available():
            return {"insights": "Gemini service not available"}
        
        try:
            prompt = f"""
            Analyze the following document and extract key insights. Provide:
            1. Main themes and topics
            2. Sentiment analysis
            3. Key facts and figures
            4. Potential action items or recommendations
            5. Important dates and deadlines
            6. Stakeholders or people mentioned
            
            Please format as JSON with these keys:
            - themes: list of main themes
            - sentiment: overall sentiment (positive/negative/neutral)
            - key_facts: list of important facts
            - action_items: list of recommended actions
            - important_dates: list of dates with context
            - stakeholders: list of people/organizations mentioned
            
            Document:
            {text[:4000]}
            
            Insights (JSON):
            """
            
            response = self.model.generate_content(
                prompt,
                generation_config=genai.types.GenerationConfig(
                    temperature=settings.GEMINI_TEMPERATURE,
                    max_output_tokens=1500
                )
            )
            
            try:
                return json.loads(response.text)
            except json.JSONDecodeError:
                return {
                    "themes": ["Could not extract themes"],
                    "sentiment": "neutral",
                    "raw_response": response.text
                }
            
        except Exception as e:
            logger.error(f"Gemini insights extraction failed: {e}")
            return {"error": f"Insights extraction failed: {str(e)}"}
    
    async def generate_report(self, document_data: Dict[str, Any]) -> str:
        """
        Generate comprehensive analysis report using Gemini.
        
        Args:
            document_data: Processed document data
            
        Returns:
            Comprehensive analysis report
        """
        if not self.is_available():
            return "Gemini service not available for report generation"
        
        try:
            prompt = f"""
            Generate a comprehensive analysis report for this document:
            
            Document: {document_data.get('file_name', 'Unknown')}
            Category: {document_data.get('classification', {}).get('category', 'Unknown')}
            Length: {len(document_data.get('text', ''))} characters
            
            Summary: {document_data.get('summary', 'No summary available')}
            
            Entities found:
            {json.dumps(document_data.get('entities', {}), indent=2)}
            
            Please create a professional analysis report that includes:
            1. Executive Summary
            2. Document Overview
            3. Key Findings
            4. Entity Analysis
            5. Recommendations
            6. Risk Assessment (if applicable)
            
            Make it detailed but accessible to business stakeholders.
            
            Analysis Report:
            """
            
            response = self.model.generate_content(
                prompt,
                generation_config=genai.types.GenerationConfig(
                    temperature=settings.GEMINI_TEMPERATURE,
                    max_output_tokens=settings.GEMINI_MAX_TOKENS
                )
            )
            
            return response.text if response.text else "Could not generate report"
            
        except Exception as e:
            logger.error(f"Gemini report generation failed: {e}")
            return f"Report generation failed: {str(e)}"

# Global instance
gemini_service = GeminiService()
