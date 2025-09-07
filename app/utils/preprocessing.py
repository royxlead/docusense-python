"""
Text preprocessing and cleaning utilities.

This module provides functions to clean and preprocess text data
for better performance in NLP models and analysis.
"""

import re
import string
import logging
from typing import List, Optional, Dict, Any
import unicodedata

logger = logging.getLogger(__name__)


def clean_text(
    text: str,
    remove_extra_whitespace: bool = True,
    remove_special_chars: bool = False,
    normalize_unicode: bool = True,
    to_lowercase: bool = False,
    preserve_newlines: bool = False
) -> str:
    """
    Clean and preprocess text for NLP processing.
    
    This function performs various text cleaning operations to improve
    the quality of text data for analysis and model processing.
    
    Args:
        text: Input text to clean
        remove_extra_whitespace: Remove extra spaces and normalize whitespace
        remove_special_chars: Remove special characters and punctuation
        normalize_unicode: Normalize unicode characters
        to_lowercase: Convert text to lowercase
        preserve_newlines: Whether to preserve line breaks
        
    Returns:
        str: Cleaned text
        
    Raises:
        ValueError: If input text is None
    """
    try:
        if text is None:
            raise ValueError("Input text cannot be None")
        
        if not isinstance(text, str):
            text = str(text)
        
        original_length = len(text)
        
        # Normalize unicode characters
        if normalize_unicode:
            text = unicodedata.normalize('NFKD', text)
        
        # Remove or replace non-printable characters
        text = ''.join(char for char in text if char.isprintable() or char.isspace())
        
        # Handle newlines
        if preserve_newlines:
            # Normalize different types of line breaks
            text = re.sub(r'\r\n|\r|\n', '\n', text)
        else:
            # Replace newlines with spaces
            text = re.sub(r'\r\n|\r|\n', ' ', text)
        
        # Remove extra whitespace
        if remove_extra_whitespace:
            # Replace multiple spaces with single space
            text = re.sub(r'\s+', ' ', text)
            text = text.strip()
        
        # Convert to lowercase
        if to_lowercase:
            text = text.lower()
        
        # Remove special characters
        if remove_special_chars:
            # Keep alphanumeric and basic punctuation
            text = re.sub(r'[^\w\s.,!?;:()\-"\']', '', text)
        
        cleaned_length = len(text)
        
        if original_length > 0:
            reduction_percent = ((original_length - cleaned_length) / original_length) * 100
            if reduction_percent > 10:  # Log significant changes
                logger.debug(f"Text cleaning reduced length by {reduction_percent:.1f}%")
        
        return text
        
    except Exception as e:
        logger.error(f"Text cleaning failed: {str(e)}")
        return str(text) if text is not None else ""


def remove_noise(
    text: str,
    remove_urls: bool = True,
    remove_emails: bool = True,
    remove_phone_numbers: bool = False,
    remove_numbers: bool = False,
    remove_html_tags: bool = True
) -> str:
    """
    Remove various types of noise from text.
    
    Args:
        text: Input text to clean
        remove_urls: Remove URLs and web addresses
        remove_emails: Remove email addresses
        remove_phone_numbers: Remove phone numbers
        remove_numbers: Remove all numbers
        remove_html_tags: Remove HTML tags
        
    Returns:
        str: Text with noise removed
    """
    try:
        if not text:
            return ""
        
        # Remove HTML tags
        if remove_html_tags:
            text = re.sub(r'<[^>]+>', '', text)
        
        # Remove URLs
        if remove_urls:
            url_pattern = r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+'
            text = re.sub(url_pattern, '', text)
            # Also remove www.domain.com patterns
            text = re.sub(r'www\.[a-zA-Z0-9\-\.]+\.[a-zA-Z]{2,}', '', text)
        
        # Remove email addresses
        if remove_emails:
            email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
            text = re.sub(email_pattern, '', text)
        
        # Remove phone numbers (basic patterns)
        if remove_phone_numbers:
            phone_patterns = [
                r'\b\d{3}[-.]?\d{3}[-.]?\d{4}\b',  # US format
                r'\b\(\d{3}\)\s?\d{3}[-.]?\d{4}\b',  # US format with parentheses
                r'\b\+\d{1,3}[-.\s]?\d{3,4}[-.\s]?\d{3,4}[-.\s]?\d{3,4}\b'  # International
            ]
            for pattern in phone_patterns:
                text = re.sub(pattern, '', text)
        
        # Remove numbers
        if remove_numbers:
            text = re.sub(r'\b\d+\b', '', text)
        
        # Clean up extra spaces
        text = re.sub(r'\s+', ' ', text).strip()
        
        return text
        
    except Exception as e:
        logger.error(f"Noise removal failed: {str(e)}")
        return text


def extract_sentences(text: str, min_length: int = 10) -> List[str]:
    """
    Extract sentences from text.
    
    Args:
        text: Input text to split into sentences
        min_length: Minimum length for a sentence to be included
        
    Returns:
        List[str]: List of sentences
    """
    try:
        if not text:
            return []
        
        # Simple sentence splitting based on punctuation
        sentences = re.split(r'[.!?]+', text)
        
        # Clean and filter sentences
        cleaned_sentences = []
        for sentence in sentences:
            sentence = sentence.strip()
            if len(sentence) >= min_length:
                cleaned_sentences.append(sentence)
        
        return cleaned_sentences
        
    except Exception as e:
        logger.error(f"Sentence extraction failed: {str(e)}")
        return []


def extract_paragraphs(text: str, min_length: int = 50) -> List[str]:
    """
    Extract paragraphs from text.
    
    Args:
        text: Input text to split into paragraphs
        min_length: Minimum length for a paragraph to be included
        
    Returns:
        List[str]: List of paragraphs
    """
    try:
        if not text:
            return []
        
        # Split by double newlines or multiple spaces
        paragraphs = re.split(r'\n\s*\n|\n{2,}', text)
        
        # Clean and filter paragraphs
        cleaned_paragraphs = []
        for paragraph in paragraphs:
            paragraph = paragraph.strip()
            if len(paragraph) >= min_length:
                cleaned_paragraphs.append(paragraph)
        
        return cleaned_paragraphs
        
    except Exception as e:
        logger.error(f"Paragraph extraction failed: {str(e)}")
        return []


def tokenize_text(text: str, preserve_case: bool = False) -> List[str]:
    """
    Simple tokenization of text into words.
    
    Args:
        text: Input text to tokenize
        preserve_case: Whether to preserve original case
        
    Returns:
        List[str]: List of tokens/words
    """
    try:
        if not text:
            return []
        
        if not preserve_case:
            text = text.lower()
        
        # Simple word tokenization
        tokens = re.findall(r'\b\w+\b', text)
        
        return tokens
        
    except Exception as e:
        logger.error(f"Tokenization failed: {str(e)}")
        return []


def remove_stopwords(tokens: List[str], custom_stopwords: Optional[List[str]] = None) -> List[str]:
    """
    Remove common stopwords from token list.
    
    Args:
        tokens: List of tokens to filter
        custom_stopwords: Additional stopwords to remove
        
    Returns:
        List[str]: Filtered list of tokens
    """
    try:
        # Basic English stopwords
        default_stopwords = {
            'a', 'an', 'and', 'are', 'as', 'at', 'be', 'by', 'for', 'from',
            'has', 'he', 'in', 'is', 'it', 'its', 'of', 'on', 'that', 'the',
            'to', 'was', 'will', 'with', 'would', 'you', 'your', 'i', 'me',
            'we', 'us', 'they', 'them', 'this', 'these', 'those', 'have',
            'had', 'been', 'being', 'do', 'does', 'did', 'can', 'could',
            'should', 'would', 'may', 'might', 'must', 'shall'
        }
        
        if custom_stopwords:
            stopwords = default_stopwords.union(set(custom_stopwords))
        else:
            stopwords = default_stopwords
        
        filtered_tokens = [token for token in tokens if token.lower() not in stopwords]
        
        return filtered_tokens
        
    except Exception as e:
        logger.error(f"Stopword removal failed: {str(e)}")
        return tokens


def normalize_whitespace(text: str) -> str:
    """
    Normalize all whitespace characters to standard spaces.
    
    Args:
        text: Input text to normalize
        
    Returns:
        str: Text with normalized whitespace
    """
    try:
        if not text:
            return ""
        
        # Replace all whitespace characters with standard space
        text = re.sub(r'\s', ' ', text)
        
        # Replace multiple spaces with single space
        text = re.sub(r' +', ' ', text)
        
        return text.strip()
        
    except Exception as e:
        logger.error(f"Whitespace normalization failed: {str(e)}")
        return text


def get_text_statistics(text: str) -> Dict[str, Any]:
    """
    Calculate various statistics about text.
    
    Args:
        text: Input text to analyze
        
    Returns:
        Dict[str, Any]: Dictionary containing text statistics
    """
    try:
        if not text:
            return {
                "character_count": 0,
                "word_count": 0,
                "sentence_count": 0,
                "paragraph_count": 0,
                "average_word_length": 0,
                "average_sentence_length": 0
            }
        
        # Basic counts
        char_count = len(text)
        words = tokenize_text(text)
        word_count = len(words)
        sentences = extract_sentences(text)
        sentence_count = len(sentences)
        paragraphs = extract_paragraphs(text)
        paragraph_count = len(paragraphs)
        
        # Averages
        avg_word_length = sum(len(word) for word in words) / word_count if word_count > 0 else 0
        avg_sentence_length = word_count / sentence_count if sentence_count > 0 else 0
        
        return {
            "character_count": char_count,
            "word_count": word_count,
            "sentence_count": sentence_count,
            "paragraph_count": paragraph_count,
            "average_word_length": round(avg_word_length, 2),
            "average_sentence_length": round(avg_sentence_length, 2),
            "readability_score": _calculate_simple_readability(sentences, words)
        }
        
    except Exception as e:
        logger.error(f"Text statistics calculation failed: {str(e)}")
        return {"error": str(e)}


def _calculate_simple_readability(sentences: List[str], words: List[str]) -> float:
    """
    Calculate a simple readability score.
    
    Args:
        sentences: List of sentences
        words: List of words
        
    Returns:
        float: Simple readability score
    """
    try:
        if not sentences or not words:
            return 0.0
        
        avg_sentence_length = len(words) / len(sentences)
        avg_word_length = sum(len(word) for word in words) / len(words)
        
        # Simple readability formula (lower is more readable)
        readability = (avg_sentence_length * 0.5) + (avg_word_length * 2)
        
        return round(readability, 2)
        
    except Exception:
        return 0.0