"""
Document Processing Service

Handles document text extraction, analysis, and accessibility features.
Provides comprehensive document processing capabilities including OCR,
content analysis, structure recognition, and accessibility enhancement.
"""

import asyncio
import logging
from typing import Dict, List, Optional, Any, Union
from datetime import datetime, timezone
import json
import re
from pathlib import Path

import numpy as np
from sqlalchemy.orm import Session

from dryad.university.database.models_university import MediaAsset, MultimodalInteraction


class DocumentProcessingService:
    """
    Service for processing documents and extracting text content.
    
    Capabilities:
    - Text extraction from various document formats
    - Document structure analysis
    - Content summarization and key topic extraction
    - Language detection and translation
    - Accessibility features (screen reader optimization)
    """
    
    def __init__(self, db: Session):
        """Initialize the document processing service"""
        self.db = db
        self.logger = logging.getLogger(__name__)
        
        # Supported document formats
        self.supported_formats = ['.pdf', '.docx', '.doc', '.txt', '.rtf', '.odt']
        
        # Model configurations (would be loaded from actual models in production)
        self.models = {
            'text_extraction': 'pdfplumber',
            'ocr': 'pytesseract',
            'language_detection': 'langdetect',
            'text_summarization': 'transformers',
            'keyword_extraction': 'nltk'
        }
        
        # Processing settings
        self.processing_settings = {
            'max_text_length': 100000,  # Maximum characters to process
            'chunk_size': 1000,  # Text chunk size for processing
            'language': 'auto'  # Default language detection
        }
    
    async def extract_text(
        self,
        document_data: Union[str, bytes],
        options: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Extract text content from documents.
        
        Args:
            document_data: Document file path or bytes
            options: Extraction options (OCR, language detection, etc.)
            
        Returns:
            Dict containing extracted text and metadata
        """
        try:
            options = options or {}
            
            # Load and validate document
            document_info = await self._load_document(document_data)
            
            # Extract text based on document type
            extraction_result = await self._extract_text_by_format(document_info, options)
            
            # Post-process extracted text
            extraction_result = await self._post_process_text(extraction_result, options)
            
            # Add metadata
            extraction_result.update({
                'timestamp': datetime.now(timezone.utc).isoformat(),
                'document_type': document_info.get('format', 'unknown'),
                'extraction_method': extraction_result.get('method', 'unknown'),
                'confidence': extraction_result.get('confidence', 0.0)
            })
            
            return extraction_result
            
        except Exception as e:
            self.logger.error(f"Error extracting text from document: {str(e)}")
            raise
    
    async def analyze_document_structure(
        self,
        extraction_results: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Analyze document structure and content organization.
        
        Args:
            extraction_results: Results from text extraction
            
        Returns:
            Dict containing structural analysis results
        """
        try:
            text_content = extraction_results.get('text', '')
            
            if not text_content:
                return {'error': 'No text content available for analysis'}
            
            # Perform various structural analyses
            results = {
                'timestamp': datetime.now(timezone.utc).isoformat(),
                'text_length': len(text_content),
                'word_count': len(text_content.split()),
                'sentence_count': len(re.findall(r'[.!?]+', text_content)),
                'paragraph_count': len(text_content.split('\n\n'))
            }
            
            # Detect document structure
            results['structure_analysis'] = await self._analyze_document_structure(text_content)
            
            # Extract headings and sections
            results['headings_sections'] = await self._extract_headings_and_sections(text_content)
            
            # Identify key topics and themes
            results['key_topics'] = await self._extract_key_topics(text_content)
            
            # Calculate readability scores
            results['readability_scores'] = await self._calculate_readability_scores(text_content)
            
            # Detect language and characteristics
            results['language_analysis'] = await self._analyze_language(text_content)
            
            # Extract metadata and references
            results['metadata_extraction'] = await self._extract_document_metadata(text_content)
            
            # Calculate overall structure score
            results['structure_score'] = self._calculate_structure_score(results)
            
            return results
            
        except Exception as e:
            self.logger.error(f"Error analyzing document structure: {str(e)}")
            raise
    
    async def analyze_text_content(
        self,
        text_content: str,
        options: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Analyze text content for various characteristics.
        
        Args:
            text_content: Text content to analyze
            options: Analysis options
            
        Returns:
            Dict containing analysis results
        """
        try:
            options = options or {}
            
            # Basic text statistics
            analysis_results = {
                'timestamp': datetime.now(timezone.utc).isoformat(),
                'text_length': len(text_content),
                'word_count': len(text_content.split()),
                'character_count': len(text_content),
                'line_count': len(text_content.splitlines())
            }
            
            # Sentiment analysis
            if options.get('analyze_sentiment', True):
                analysis_results['sentiment'] = await self._analyze_sentiment(text_content)
            
            # Named entity recognition
            if options.get('extract_entities', True):
                analysis_results['entities'] = await self._extract_named_entities(text_content)
            
            # Keyword extraction
            if options.get('extract_keywords', True):
                analysis_results['keywords'] = await self._extract_keywords(text_content)
            
            # Language detection
            analysis_results['language'] = await self._detect_language(text_content)
            
            # Content categorization
            if options.get('categorize_content', True):
                analysis_results['content_category'] = await self._categorize_content(text_content)
            
            # Calculate confidence scores
            analysis_results['confidence_scores'] = self._calculate_text_confidence_scores(analysis_results)
            analysis_results['overall_confidence'] = np.mean(list(analysis_results['confidence_scores'].values()))
            
            return analysis_results
            
        except Exception as e:
            self.logger.error(f"Error analyzing text content: {str(e)}")
            raise
    
    async def generate_accessibility_features(
        self,
        extraction_results: Dict[str, Any],
        analysis_results: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Generate accessibility features for document content.
        
        Args:
            extraction_results: Results from text extraction
            analysis_results: Results from document analysis
            
        Returns:
            Dict containing accessibility features
        """
        try:
            accessibility_features = {}
            
            # Generate structured text for screen readers
            accessibility_features['screen_reader_text'] = self._generate_screen_reader_text(
                extraction_results, analysis_results
            )
            
            # Create table of contents
            if analysis_results.get('headings_sections'):
                accessibility_features['table_of_contents'] = self._generate_table_of_contents(
                    analysis_results['headings_sections']
                )
            
            # Generate alt text for images/figures
            if extraction_results.get('images') or extraction_results.get('figures'):
                accessibility_features['image_descriptions'] = self._generate_image_descriptions(
                    extraction_results
                )
            
            # Create navigation aids
            accessibility_features['navigation_aids'] = self._generate_navigation_aids(
                analysis_results
            )
            
            # Accessibility score
            accessibility_features['accessibility_score'] = self._calculate_document_accessibility_score(
                accessibility_features
            )
            
            # Recommendations
            accessibility_features['recommendations'] = self._generate_document_accessibility_recommendations(
                extraction_results, analysis_results
            )
            
            return accessibility_features
            
        except Exception as e:
            self.logger.error(f"Error generating accessibility features: {str(e)}")
            raise
    
    async def generate_text_accessibility_features(
        self,
        text_content: str,
        analysis_results: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Generate accessibility features specifically for plain text content.
        
        Args:
            text_content: Text content
            analysis_results: Results from text analysis
            
        Returns:
            Dict containing text accessibility features
        """
        try:
            accessibility_features = {}
            
            # Optimize text structure
            accessibility_features['structured_text'] = self._optimize_text_structure(text_content)
            
            # Generate reading guide
            if analysis_results.get('key_topics'):
                accessibility_features['reading_guide'] = self._generate_reading_guide(analysis_results)
            
            # Create content warnings if needed
            accessibility_features['content_warnings'] = self._detect_text_content_warnings(text_content)
            
            # Accessibility score
            accessibility_features['accessibility_score'] = self._calculate_text_accessibility_score(accessibility_features)
            
            # Provide accessibility recommendations
            accessibility_features['recommendations'] = self._generate_text_accessibility_recommendations(
                text_content, analysis_results
            )
            
            return accessibility_features
            
        except Exception as e:
            self.logger.error(f"Error generating text accessibility features: {str(e)}")
            raise
    
    async def _load_document(self, document_data: Union[str, bytes]) -> Dict[str, Any]:
        """Load and validate document"""
        try:
            if isinstance(document_data, str):
                # Load from file path
                file_path = Path(document_data)
                document_info = {
                    'file_path': document_data,
                    'format': file_path.suffix.lower(),
                    'file_size': file_path.stat().st_size if file_path.exists() else 0,
                    'filename': file_path.name
                }
            elif isinstance(document_data, bytes):
                # Load from bytes (mock implementation)
                document_info = {
                    'format': '.pdf',  # Default assumption
                    'file_size': len(document_data),
                    'filename': 'document.pdf'
                }
            else:
                raise ValueError("Invalid document data type")
            
            return document_info
            
        except Exception as e:
            self.logger.error(f"Error loading document: {str(e)}")
            raise
    
    async def _extract_text_by_format(
        self,
        document_info: Dict[str, Any],
        options: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Extract text based on document format"""
        format_type = document_info.get('format', '').lower()
        
        if format_type == '.pdf':
            return await self._extract_from_pdf(document_info, options)
        elif format_type in ['.docx', '.doc']:
            return await self._extract_from_word(document_info, options)
        elif format_type == '.txt':
            return await self._extract_from_text(document_info, options)
        else:
            return await self._extract_generic_text(document_info, options)
    
    async def _extract_from_pdf(
        self,
        document_info: Dict[str, Any],
        options: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Extract text from PDF documents (mock implementation)"""
        # In production, would use pdfplumber, PyPDF2, or similar
        return {
            'text': "This is extracted text from a PDF document. The document contains various sections with headings, paragraphs, and possibly images.",
            'pages': 3,
            'method': 'pdf_extraction',
            'confidence': 0.92,
            'images': [
                {'page': 1, 'description': 'Chart showing data trends'}
            ]
        }
    
    async def _extract_from_word(
        self,
        document_info: Dict[str, Any],
        options: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Extract text from Word documents (mock implementation)"""
        # In production, would use python-docx or similar
        return {
            'text': "This is extracted text from a Word document. It includes formatted text, tables, and embedded images.",
            'method': 'word_extraction',
            'confidence': 0.95,
            'tables': [
                {'rows': 5, 'columns': 3, 'content': 'Sample table data'}
            ]
        }
    
    async def _extract_from_text(
        self,
        document_info: Dict[str, Any],
        options: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Extract text from plain text files"""
        try:
            if isinstance(document_info.get('file_path'), str):
                with open(document_info['file_path'], 'r', encoding='utf-8') as f:
                    text = f.read()
                
                return {
                    'text': text,
                    'method': 'plain_text_extraction',
                    'confidence': 1.0,
                    'encoding': 'utf-8'
                }
            else:
                raise ValueError("Text file extraction requires file path")
                
        except Exception as e:
            self.logger.error(f"Error extracting from text file: {str(e)}")
            raise
    
    async def _extract_generic_text(
        self,
        document_info: Dict[str, Any],
        options: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Generic text extraction for unsupported formats"""
        return {
            'text': "Unable to extract text from this document format. Consider converting to PDF or plain text.",
            'method': 'generic_extraction',
            'confidence': 0.1,
            'error': 'Unsupported format'
        }
    
    async def _post_process_text(
        self,
        extraction_result: Dict[str, Any],
        options: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Post-process extracted text"""
        text = extraction_result.get('text', '')
        
        if not text:
            return extraction_result
        
        # Clean text
        cleaned_text = self._clean_text(text)
        
        # Handle OCR if enabled
        if options.get('enable_ocr', False):
            cleaned_text = await self._apply_ocr_corrections(cleaned_text)
        
        # Apply language-specific processing
        if options.get('language') and options['language'] != 'auto':
            cleaned_text = await self._apply_language_specific_processing(
                cleaned_text, options['language']
            )
        
        extraction_result['text'] = cleaned_text
        return extraction_result
    
    def _clean_text(self, text: str) -> str:
        """Clean and normalize extracted text"""
        # Remove excessive whitespace
        text = re.sub(r'\s+', ' ', text)
        
        # Fix common OCR errors
        text = re.sub(r'\|', 'l', text)  # Convert pipe to lowercase L
        text = re.sub(r'0', 'O', text)   # Fix zero/O confusion in certain contexts
        
        # Normalize line breaks
        text = re.sub(r'\n\s*\n', '\n\n', text)
        
        return text.strip()
    
    async def _apply_ocr_corrections(self, text: str) -> str:
        """Apply OCR-specific corrections (mock implementation)"""
        # In production, would use language models for OCR correction
        return text
    
    async def _apply_language_specific_processing(self, text: str, language: str) -> str:
        """Apply language-specific text processing"""
        # In production, would use language-specific libraries
        return text
    
    async def _analyze_document_structure(self, text: str) -> Dict[str, Any]:
        """Analyze document structure and organization"""
        # Detect headings
        heading_patterns = [
            r'^#{1,6}\s+.+$',  # Markdown headings
            r'^[A-Z][^.!?]*$',  # Potential headings
            r'^\d+\.?\s+.+$'   # Numbered sections
        ]
        
        headings = []
        for pattern in heading_patterns:
            matches = re.findall(pattern, text, re.MULTILINE)
            headings.extend(matches)
        
        # Detect lists
        list_patterns = [
            r'^[\s]*[-*+]\s+.+$',  # Bullet lists
            r'^[\s]*\d+\.?\s+.+$', # Numbered lists
        ]
        
        lists = []
        for pattern in list_patterns:
            matches = re.findall(pattern, text, re.MULTILINE)
            lists.extend(matches)
        
        return {
            'has_headings': len(headings) > 0,
            'heading_count': len(headings),
            'has_lists': len(lists) > 0,
            'list_count': len(lists),
            'structure_type': self._classify_document_structure(headings, lists),
            'complexity_score': min(1.0, (len(headings) + len(lists)) / 20)
        }
    
    def _classify_document_structure(self, headings: List[str], lists: List[str]) -> str:
        """Classify document structure type"""
        heading_ratio = len(headings) / max(1, len(headings) + len(lists))
        
        if heading_ratio > 0.7:
            return 'structured'
        elif heading_ratio > 0.3:
            return 'mixed'
        else:
            return 'narrative'
    
    async def _extract_headings_and_sections(self, text: str) -> List[Dict[str, Any]]:
        """Extract headings and section information"""
        sections = []
        
        # Simple section detection based on patterns
        lines = text.split('\n')
        current_section = None
        
        for i, line in enumerate(lines):
            line = line.strip()
            if not line:
                continue
            
            # Check if line looks like a heading
            if (len(line) < 100 and 
                (line.isupper() or 
                 line.endswith(':') or 
                 re.match(r'^\d+\.?\s+', line))):
                
                if current_section:
                    sections.append(current_section)
                
                current_section = {
                    'title': line,
                    'line_number': i + 1,
                    'content_preview': '',
                    'word_count': 0
                }
            elif current_section:
                # Add content to current section
                if not current_section['content_preview']:
                    current_section['content_preview'] = line[:100]
                current_section['word_count'] += len(line.split())
        
        # Add last section
        if current_section:
            sections.append(current_section)
        
        return sections
    
    async def _extract_key_topics(self, text: str) -> List[Dict[str, Any]]:
        """Extract key topics and themes from text"""
        # Simple keyword extraction (would use more sophisticated methods in production)
        words = re.findall(r'\b[A-Za-z]{4,}\b', text.lower())
        word_freq = {}
        
        for word in words:
            if word not in ['this', 'that', 'with', 'from', 'they', 'have', 'been', 'were', 'said']:
                word_freq[word] = word_freq.get(word, 0) + 1
        
        # Get top keywords
        top_words = sorted(word_freq.items(), key=lambda x: x[1], reverse=True)[:10]
        
        topics = []
        for word, freq in top_words:
            topics.append({
                'topic': word,
                'frequency': freq,
                'relevance_score': min(1.0, freq / max(1, max(word_freq.values())))
            })
        
        return topics
    
    async def _calculate_readability_scores(self, text: str) -> Dict[str, float]:
        """Calculate various readability scores"""
        # Simple readability metrics
        sentences = re.split(r'[.!?]+', text)
        words = text.split()
        
        if not sentences or not words:
            return {'flesch_score': 0.0, 'grade_level': 0.0}
        
        # Basic calculations
        avg_sentence_length = len(words) / len(sentences)
        avg_word_length = sum(len(word) for word in words) / len(words)
        
        # Mock Flesch Reading Ease Score
        flesch_score = max(0, min(100, 206.835 - (1.015 * avg_sentence_length) - (84.6 * avg_word_length / 4.6)))
        
        # Mock grade level
        grade_level = max(1, min(12, (avg_sentence_length * 0.39) + (avg_word_length * 11.8) - 15.59))
        
        return {
            'flesch_score': flesch_score,
            'grade_level': grade_level,
            'avg_sentence_length': avg_sentence_length,
            'avg_word_length': avg_word_length
        }
    
    async def _analyze_language(self, text: str) -> Dict[str, Any]:
        """Analyze language characteristics"""
        # Mock language detection
        english_indicators = ['the', 'and', 'is', 'in', 'to', 'of', 'a', 'that', 'it', 'with']
        text_words = text.lower().split()
        
        english_score = sum(1 for word in text_words if word in english_indicators) / max(1, len(text_words))
        
        return {
            'detected_language': 'en' if english_score > 0.02 else 'unknown',
            'language_confidence': english_score,
            'characteristics': {
                'has_punctuation': bool(re.search(r'[.!?]', text)),
                'has_numbers': bool(re.search(r'\d', text)),
                'has_special_chars': bool(re.search(r'[^a-zA-Z\s]', text))
            }
        }
    
    async def _extract_document_metadata(self, text: str) -> Dict[str, Any]:
        """Extract metadata and references from document"""
        metadata = {
            'references': [],
            'citations': [],
            'urls': [],
            'emails': [],
            'dates': []
        }
        
        # Extract URLs
        url_pattern = r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+'
        metadata['urls'] = re.findall(url_pattern, text)
        
        # Extract email addresses
        email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        metadata['emails'] = re.findall(email_pattern, text)
        
        # Extract dates
        date_pattern = r'\b\d{1,2}[/-]\d{1,2}[/-]\d{2,4}\b|\b\d{4}[/-]\d{1,2}[/-]\d{1,2}\b'
        metadata['dates'] = re.findall(date_pattern, text)
        
        return metadata
    
    def _calculate_structure_score(self, results: Dict[str, Any]) -> float:
        """Calculate overall document structure score"""
        score = 0.0
        
        structure = results.get('structure_analysis', {})
        headings = results.get('headings_sections', [])
        readability = results.get('readability_scores', {})
        
        # Score based on structural elements
        if structure.get('has_headings'):
            score += 0.3
        if structure.get('has_lists'):
            score += 0.2
        
        # Score based on heading count
        if headings:
            score += min(0.3, len(headings) * 0.05)
        
        # Score based on readability
        flesch = readability.get('flesch_score', 0)
        if flesch > 60:  # Good readability
            score += 0.2
        elif flesch > 30:  # Moderate readability
            score += 0.1
        
        return min(1.0, score)
    
    async def _analyze_sentiment(self, text: str) -> Dict[str, Any]:
        """Analyze sentiment of text content"""
        # Mock sentiment analysis
        positive_words = ['good', 'great', 'excellent', 'wonderful', 'amazing', 'fantastic']
        negative_words = ['bad', 'terrible', 'awful', 'horrible', 'disgusting', 'worst']
        
        words = text.lower().split()
        positive_count = sum(1 for word in words if word in positive_words)
        negative_count = sum(1 for word in words if word in negative_words)
        
        total_words = len(words)
        positive_score = positive_count / max(1, total_words)
        negative_score = negative_count / max(1, total_words)
        
        # Determine overall sentiment
        if positive_score > negative_score:
            sentiment = 'positive'
        elif negative_score > positive_score:
            sentiment = 'negative'
        else:
            sentiment = 'neutral'
        
        return {
            'sentiment': sentiment,
            'positive_score': positive_score,
            'negative_score': negative_score,
            'confidence': abs(positive_score - negative_score) * 10
        }
    
    async def _extract_named_entities(self, text: str) -> List[Dict[str, Any]]:
        """Extract named entities from text"""
        # Mock named entity recognition
        entities = []
        
        # Simple patterns for common entities
        person_pattern = r'\b[A-Z][a-z]+ [A-Z][a-z]+\b'
        organization_pattern = r'\b[A-Z][a-z]+ (Inc|Corp|Ltd|University|College|School)\b'
        location_pattern = r'\b(New York|Los Angeles|Chicago|Houston|Phoenix|Philadelphia|San Antonio|San Diego|Dallas|San Jose)\b'
        
        persons = re.findall(person_pattern, text)
        organizations = re.findall(organization_pattern, text)
        locations = re.findall(location_pattern, text)
        
        for person in persons[:5]:  # Limit results
            entities.append({'text': person, 'label': 'PERSON', 'confidence': 0.8})
        
        for org in organizations[:3]:
            entities.append({'text': org, 'label': 'ORG', 'confidence': 0.7})
        
        for loc in locations[:3]:
            entities.append({'text': loc, 'label': 'LOCATION', 'confidence': 0.9})
        
        return entities
    
    async def _extract_keywords(self, text: str) -> List[Dict[str, Any]]:
        """Extract keywords from text"""
        # Simple keyword extraction
        words = re.findall(r'\b[A-Za-z]{4,}\b', text.lower())
        
        # Filter common words
        stop_words = {'this', 'that', 'with', 'from', 'they', 'have', 'been', 'were', 'said', 'each', 'which', 'their', 'time'}
        filtered_words = [word for word in words if word not in stop_words]
        
        # Count frequencies
        word_freq = {}
        for word in filtered_words:
            word_freq[word] = word_freq.get(word, 0) + 1
        
        # Get top keywords
        keywords = sorted(word_freq.items(), key=lambda x: x[1], reverse=True)[:10]
        
        return [{'keyword': word, 'frequency': freq, 'score': freq / max(1, max(word_freq.values()))} 
                for word, freq in keywords]
    
    async def _detect_language(self, text: str) -> str:
        """Detect language of text"""
        # Mock language detection
        english_common = ['the', 'and', 'is', 'in', 'to', 'of', 'a', 'that', 'it', 'with']
        text_words = text.lower().split()
        
        english_indicators = sum(1 for word in text_words if word in english_common)
        english_ratio = english_indicators / max(1, len(text_words))
        
        return 'en' if english_ratio > 0.02 else 'unknown'
    
    async def _categorize_content(self, text: str) -> Dict[str, Any]:
        """Categorize content type and domain"""
        categories = {
            'academic': 0,
            'technical': 0,
            'business': 0,
            'creative': 0,
            'news': 0
        }
        
        # Simple keyword-based categorization
        academic_keywords = ['research', 'study', 'analysis', 'hypothesis', 'methodology', 'university']
        technical_keywords = ['algorithm', 'code', 'programming', 'software', 'system', 'database']
        business_keywords = ['market', 'revenue', 'profit', 'strategy', 'customer', 'business']
        creative_keywords = ['story', 'creative', 'imagination', 'art', 'design', 'artistic']
        news_keywords = ['reported', 'breaking', 'news', 'according', 'sources', 'yesterday']
        
        text_lower = text.lower()
        
        for keyword in academic_keywords:
            if keyword in text_lower:
                categories['academic'] += 1
        
        for keyword in technical_keywords:
            if keyword in text_lower:
                categories['technical'] += 1
        
        for keyword in business_keywords:
            if keyword in text_lower:
                categories['business'] += 1
        
        for keyword in creative_keywords:
            if keyword in text_lower:
                categories['creative'] += 1
        
        for keyword in news_keywords:
            if keyword in text_lower:
                categories['news'] += 1
        
        # Determine primary category
        primary_category = max(categories.items(), key=lambda x: x[1])
        
        return {
            'primary_category': primary_category[0] if primary_category[1] > 0 else 'general',
            'category_scores': categories,
            'confidence': primary_category[1] / max(1, sum(categories.values()))
        }
    
    def _calculate_text_confidence_scores(self, analysis_results: Dict[str, Any]) -> Dict[str, float]:
        """Calculate confidence scores for different analysis types"""
        confidence_scores = {}
        
        # Sentiment confidence
        sentiment = analysis_results.get('sentiment', {})
        confidence_scores['sentiment'] = sentiment.get('confidence', 0.0)
        
        # Language detection confidence
        language_confidence = analysis_results.get('language_analysis', {}).get('language_confidence', 0.0)
        confidence_scores['language_detection'] = language_confidence
        
        # Entity recognition confidence
        entities = analysis_results.get('entities', [])
        if entities:
            entity_confidences = [entity.get('confidence', 0.0) for entity in entities]
            confidence_scores['entity_recognition'] = np.mean(entity_confidences)
        else:
            confidence_scores['entity_recognition'] = 0.0
        
        # Keyword extraction confidence
        keywords = analysis_results.get('keywords', [])
        if keywords:
            confidence_scores['keyword_extraction'] = np.mean([k.get('score', 0.0) for k in keywords])
        else:
            confidence_scores['keyword_extraction'] = 0.0
        
        return confidence_scores
    
    def _generate_screen_reader_text(
        self,
        extraction_results: Dict[str, Any],
        analysis_results: Dict[str, Any]
    ) -> str:
        """Generate optimized text for screen readers"""
        text_parts = []
        
        # Document metadata
        doc_type = extraction_results.get('document_type', 'document')
        text_parts.append(f"Document type: {doc_type}")
        
        # Table of contents if available
        if analysis_results.get('headings_sections'):
            headings = analysis_results['headings_sections']
            text_parts.append("Table of contents:")
            for heading in headings[:10]:  # Limit to avoid overwhelming
                text_parts.append(f"  {heading['title']}")
        
        # Main content
        main_text = extraction_results.get('text', '')
        if main_text:
            text_parts.append("Document content follows:")
            text_parts.append(main_text)
        
        return '\n'.join(text_parts)
    
    def _generate_table_of_contents(self, headings_sections: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Generate table of contents from headings"""
        toc = []
        
        for section in headings_sections:
            toc.append({
                'title': section['title'],
                'line_number': section['line_number'],
                'word_count': section.get('word_count', 0)
            })
        
        return toc
    
    def _generate_image_descriptions(self, extraction_results: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate descriptions for images and figures"""
        descriptions = []
        
        # Process images
        images = extraction_results.get('images', [])
        for image in images:
            descriptions.append({
                'type': 'image',
                'location': f"Page {image.get('page', 'unknown')}",
                'description': image.get('description', 'Image with no description available'),
                'accessibility_text': f"Image on page {image.get('page', 'unknown')}: {image.get('description', 'no description')}"
            })
        
        # Process figures (similar structure)
        figures = extraction_results.get('figures', [])
        for figure in figures:
            descriptions.append({
                'type': 'figure',
                'description': figure.get('description', 'Figure with no description available'),
                'accessibility_text': f"Figure: {figure.get('description', 'no description')}"
            })
        
        return descriptions
    
    def _generate_navigation_aids(self, analysis_results: Dict[str, Any]) -> Dict[str, Any]:
        """Generate navigation aids for accessibility"""
        navigation_aids = {
            'document_landmarks': [],
            'headings_list': [],
            'reading_order': 'sequential'
        }
        
        # Document landmarks
        headings = analysis_results.get('headings_sections', [])
        for heading in headings:
            navigation_aids['headings_list'].append({
                'text': heading['title'],
                'level': 'h2',  # Assume level 2
                'line_number': heading['line_number']
            })
        
        # Section landmarks
        if len(headings) > 0:
            navigation_aids['document_landmarks'] = [
                {'role': 'main', 'description': 'Main document content'},
                {'role': 'navigation', 'description': 'Document sections and headings'}
            ]
        
        return navigation_aids
    
    def _calculate_document_accessibility_score(self, features: Dict[str, Any]) -> float:
        """Calculate overall document accessibility score"""
        score = 0.0
        
        # Screen reader optimization
        if features.get('screen_reader_text'):
            score += 0.3
        
        # Table of contents
        if features.get('table_of_contents'):
            score += 0.25
        
        # Image descriptions
        if features.get('image_descriptions'):
            score += 0.2
        
        # Navigation aids
        if features.get('navigation_aids'):
            score += 0.25
        
        return min(1.0, score)
    
    def _generate_document_accessibility_recommendations(
        self,
        extraction_results: Dict[str, Any],
        analysis_results: Dict[str, Any]
    ) -> List[str]:
        """Generate accessibility recommendations for documents"""
        recommendations = []
        
        # Check for structure
        if not analysis_results.get('headings_sections'):
            recommendations.append("Add proper headings to improve document structure")
        
        # Check for images without descriptions
        if (extraction_results.get('images') or extraction_results.get('figures')) and not extraction_results.get('image_descriptions'):
            recommendations.append("Add alt text or descriptions for all images and figures")
        
        # Check for readability
        readability = analysis_results.get('readability_scores', {})
        flesch_score = readability.get('flesch_score', 0)
        if flesch_score < 30:
            recommendations.append("Improve document readability by simplifying language and sentence structure")
        
        # Check for document metadata
        metadata = analysis_results.get('metadata_extraction', {})
        if not metadata.get('references') and not metadata.get('citations'):
            recommendations.append("Consider adding references and citations where appropriate")
        
        return recommendations
    
    def _optimize_text_structure(self, text_content: str) -> str:
        """Optimize text structure for accessibility"""
        # Add proper paragraph breaks
        text = re.sub(r'\n{3,}', '\n\n', text)  # Max 2 consecutive newlines
        
        # Ensure proper spacing after sentences
        text = re.sub(r'([.!?])([A-Z])', r'\1 \2', text)
        
        # Add line breaks for long lines (readability)
        lines = text.split('\n')
        optimized_lines = []
        
        for line in lines:
            if len(line) > 80:  # Wrap long lines
                words = line.split()
                wrapped_line = ''
                current_length = 0
                
                for word in words:
                    if current_length + len(word) + 1 <= 80:
                        wrapped_line += word + ' '
                        current_length += len(word) + 1
                    else:
                        if wrapped_line:
                            optimized_lines.append(wrapped_line.strip())
                        wrapped_line = word + ' '
                        current_length = len(word) + 1
                
                if wrapped_line:
                    optimized_lines.append(wrapped_line.strip())
            else:
                optimized_lines.append(line)
        
        return '\n'.join(optimized_lines)
    
    def _generate_reading_guide(self, analysis_results: Dict[str, Any]) -> Dict[str, Any]:
        """Generate reading guide for text content"""
        key_topics = analysis_results.get('key_topics', [])
        headings = analysis_results.get('headings_sections', [])
        
        reading_guide = {
            'estimated_reading_time_minutes': max(1, analysis_results.get('word_count', 0) // 200),
            'key_points': [topic['topic'] for topic in key_topics[:5]],
            'main_sections': [heading['title'] for heading in headings[:5]],
            'reading_order': 'sequential'
        }
        
        return reading_guide
    
    def _detect_text_content_warnings(self, text_content: str) -> List[str]:
        """Detect content warnings in text"""
        warnings = []
        
        warning_patterns = {
            'sensitive_content': ['sensitive', 'trigger warning', 'content warning'],
            'mature_content': ['mature', 'adult', 'explicit'],
            'medical_content': ['medical', 'health', 'treatment', 'diagnosis'],
            'legal_content': ['legal', 'law', 'court', 'attorney']
        }
        
        text_lower = text_content.lower()
        
        for warning_type, patterns in warning_patterns.items():
            if any(pattern in text_lower for pattern in patterns):
                warnings.append(warning_type)
        
        return warnings
    
    def _calculate_text_accessibility_score(self, features: Dict[str, Any]) -> float:
        """Calculate accessibility score for text content"""
        score = 0.0
        
        # Structured text
        if features.get('structured_text'):
            score += 0.4
        
        # Reading guide
        if features.get('reading_guide'):
            score += 0.3
        
        # Content warnings
        if features.get('content_warnings'):
            score += 0.3
        
        return min(1.0, score)
    
    def _generate_text_accessibility_recommendations(
        self,
        text_content: str,
        analysis_results: Dict[str, Any]
    ) -> List[str]:
        """Generate accessibility recommendations for text content"""
        recommendations = []
        
        # Check text length
        if len(text_content) > 10000:
            recommendations.append("Consider breaking long text into smaller sections")
        
        # Check readability
        readability = analysis_results.get('readability_scores', {})
        grade_level = readability.get('grade_level', 0)
        if grade_level > 12:
            recommendations.append("Consider simplifying language for better accessibility")
        
        # Check for proper structure
        lines = text_content.split('\n')
        avg_line_length = sum(len(line) for line in lines) / max(1, len(lines))
        if avg_line_length > 80:
            recommendations.append("Consider breaking long lines for better readability")
        
        # Check for headings
        if not analysis_results.get('key_topics'):
            recommendations.append("Consider adding section headings or key topic indicators")
        
        return recommendations