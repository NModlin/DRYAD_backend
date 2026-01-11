"""
Memory Scribe Agent - Level 1 Component

Content ingestion and transformation agent for the Memory Guild.
Processes raw content, generates embeddings, extracts metadata, and handles deduplication.

Part of DRYAD.AI Agent Evolution Architecture Level 1.
"""

import asyncio
import hashlib
import uuid
import re
from datetime import datetime
from enum import Enum
from typing import Dict, Any, Optional, List, Union
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field

from dryad.services.logging.logger import StructuredLogger
from dryad.services.memory_guild.models import MemoryRecord
from dryad.services.memory_guild.coordinator import MemoryCoordinatorAgent, MemoryRequest, MemoryOperation, MemoryType

logger = StructuredLogger("memory_scribe")


class ContentSource(str, Enum):
    """Types of content sources."""
    EXECUTION_RESULT = "execution_result"
    DOCUMENTATION = "documentation"
    USER_INPUT = "user_input"
    EXTERNAL_API = "external_api"
    FILE_UPLOAD = "file_upload"
    WEB_SCRAPE = "web_scrape"
    CONVERSATION = "conversation"


def map_content_source_to_db_type(source: ContentSource) -> str:
    """
    Map ContentSource enum to database source_type values.

    Database CHECK constraint allows: 'conversation', 'tool_output', 'document', 'observation', 'external'
    """
    mapping = {
        ContentSource.EXECUTION_RESULT: "tool_output",
        ContentSource.DOCUMENTATION: "document",
        ContentSource.USER_INPUT: "conversation",
        ContentSource.EXTERNAL_API: "external",
        ContentSource.FILE_UPLOAD: "document",
        ContentSource.WEB_SCRAPE: "external",
        ContentSource.CONVERSATION: "conversation",
    }
    return mapping.get(source, "observation")


class ContentType(str, Enum):
    """Types of content."""
    TEXT = "text"
    CODE = "code"
    JSON = "json"
    MARKDOWN = "markdown"
    HTML = "html"
    CSV = "csv"
    MIXED = "mixed"


class IngestionRequest(BaseModel):
    """Content ingestion request schema."""
    content: str = Field(..., description="Raw content to ingest")
    source: ContentSource = Field(..., description="Source of the content")
    content_type: ContentType = Field(ContentType.TEXT, description="Type of content")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Additional metadata")
    tenant_id: Optional[str] = Field(None, description="Tenant identifier")
    agent_id: Optional[str] = Field(None, description="Agent identifier")
    priority: int = Field(5, description="Processing priority (1-10)")
    deduplicate: bool = Field(True, description="Enable deduplication")


class IngestionResult(BaseModel):
    """Content ingestion result schema."""
    success: bool
    memory_id: Optional[str] = None
    content_hash: Optional[str] = None
    extracted_metadata: Optional[Dict[str, Any]] = None
    embedding_dimensions: Optional[int] = None
    duplicate_detected: bool = False
    processing_time_ms: Optional[int] = None
    error: Optional[str] = None


class ExtractedContent(BaseModel):
    """Extracted and processed content."""
    title: Optional[str] = None
    summary: str
    key_points: List[str] = []
    entities: List[str] = []
    topics: List[str] = []
    sentiment: Optional[str] = None
    language: str = "en"
    confidence_score: float = 1.0


class MemoryScribeAgent:
    """
    Level 1 Component: Memory Scribe Agent
    
    Responsible for content ingestion and transformation in the Memory Guild.
    Processes raw content, generates embeddings, extracts metadata, and handles
    deduplication before storing in appropriate memory systems.
    """
    
    def __init__(self, db: Session, coordinator: Optional[MemoryCoordinatorAgent] = None):
        self.db = db
        self.coordinator = coordinator or MemoryCoordinatorAgent(db)
        
        # Configuration
        self.max_content_length = 1000000  # 1MB
        self.embedding_model = "text-embedding-3-small"  # Default embedding model
        self.embedding_dimensions = 1536
        self.batch_size = 50
        
        # Mock embedding service (Level 2 will implement actual service)
        self.embedding_service_available = False
        
        logger.log_info(
            "memory_scribe_initialized",
            {
                "embedding_model": self.embedding_model,
                "embedding_dimensions": self.embedding_dimensions,
                "embedding_service_available": self.embedding_service_available
            }
        )
    
    async def ingest_content(
        self,
        request: IngestionRequest
    ) -> IngestionResult:
        """
        Ingest and process content for storage in Memory Guild.
        
        Main entry point for content ingestion that handles the complete pipeline:
        extraction, deduplication, embedding generation, and storage.
        """
        start_time = datetime.now()
        
        try:
            # Validate content
            await self._validate_content(request)
            
            # Generate content hash for deduplication
            content_hash = self._generate_content_hash(request.content)
            
            # Check for duplicates if enabled
            duplicate_detected = False
            existing_memory_id = None
            if request.deduplicate:
                duplicate_detected, existing_memory_id = await self._check_duplicate(content_hash, request.tenant_id, request.agent_id or "scribe")  # Fixed: pass agent_id with default
                if duplicate_detected:
                    logger.log_info(
                        "duplicate_content_detected",
                        {"content_hash": content_hash, "tenant_id": request.tenant_id, "existing_memory_id": existing_memory_id}
                    )

                    processing_time = (datetime.now() - start_time).total_seconds() * 1000
                    return IngestionResult(
                        success=True,
                        memory_id=existing_memory_id,  # Return existing memory_id for duplicates
                        content_hash=content_hash,
                        duplicate_detected=True,
                        processing_time_ms=int(processing_time)
                    )
            
            # Extract metadata and key information
            extracted = await self._extract_content_metadata(request)
            
            # Generate embeddings
            embeddings = await self._generate_embeddings(request.content, extracted.summary)
            
            # Store in memory systems
            memory_id = await self._store_processed_content(
                request, extracted, embeddings, content_hash
            )
            
            processing_time = (datetime.now() - start_time).total_seconds() * 1000
            
            logger.log_info(
                "content_ingestion_completed",
                {
                    "memory_id": memory_id,
                    "content_hash": content_hash,
                    "processing_time_ms": int(processing_time),
                    "source": request.source,
                    "content_type": request.content_type
                }
            )
            
            return IngestionResult(
                success=True,
                memory_id=memory_id,
                content_hash=content_hash,
                extracted_metadata=extracted.model_dump(),  # Fixed: Pydantic v2 compatibility
                embedding_dimensions=self.embedding_dimensions,
                duplicate_detected=False,
                processing_time_ms=int(processing_time)
            )
            
        except Exception as e:
            processing_time = (datetime.now() - start_time).total_seconds() * 1000

            logger.log_error(
                "content_ingestion_failed",
                {
                    "error": str(e),
                    "error_type": type(e).__name__,
                    "source": request.source,
                    "content_type": request.content_type,
                    "tenant_id": request.tenant_id,
                    "agent_id": request.agent_id,
                    "processing_time_ms": int(processing_time)
                }
            )
            
            return IngestionResult(
                success=False,
                error=str(e),
                processing_time_ms=int(processing_time)
            )
    
    async def ingest_batch(
        self,
        requests: List[IngestionRequest]
    ) -> List[IngestionResult]:
        """
        Ingest multiple content items in batch for efficiency.
        
        Processes content in parallel while respecting batch size limits.
        """
        logger.log_info(
            "batch_ingestion_started",
            {"batch_size": len(requests), "max_batch_size": self.batch_size}
        )
        
        # Split into chunks if needed
        chunks = [
            requests[i:i + self.batch_size] 
            for i in range(0, len(requests), self.batch_size)
        ]
        
        all_results = []
        for chunk in chunks:
            # Process chunk in parallel
            tasks = [self.ingest_content(request) for request in chunk]
            chunk_results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Handle exceptions
            for i, result in enumerate(chunk_results):
                if isinstance(result, Exception):
                    chunk_results[i] = IngestionResult(
                        success=False,
                        error=str(result)
                    )
            
            all_results.extend(chunk_results)
        
        successful = sum(1 for r in all_results if r.success)
        logger.log_info(
            "batch_ingestion_completed",
            {
                "total_items": len(requests),
                "successful": successful,
                "failed": len(requests) - successful
            }
        )
        
        return all_results
    
    async def _validate_content(self, request: IngestionRequest) -> None:
        """Validate content before processing."""
        
        if not request.content or not request.content.strip():
            raise ValueError("Content cannot be empty")
        
        if len(request.content) > self.max_content_length:
            raise ValueError(f"Content exceeds maximum length: {self.max_content_length}")
        
        if not request.source:
            raise ValueError("Content source is required")
    
    def _generate_content_hash(self, content: str) -> str:
        """Generate SHA-256 hash of content for deduplication."""
        
        # Normalize content for consistent hashing
        normalized = re.sub(r'\s+', ' ', content.strip().lower())
        
        return hashlib.sha256(normalized.encode('utf-8')).hexdigest()
    
    async def _check_duplicate(self, content_hash: str, tenant_id: str, agent_id: str) -> tuple[bool, Optional[str]]:
        """
        Check if content hash already exists for tenant and agent.

        Returns:
            tuple: (is_duplicate, existing_memory_id)
        """

        try:
            existing = self.db.query(MemoryRecord).filter(
                MemoryRecord.content_hash == content_hash,
                MemoryRecord.tenant_id == (tenant_id or "default"),  # Fixed: proper parentheses
                MemoryRecord.agent_id == agent_id  # Fixed: also check agent_id for UNIQUE constraint
            ).first()

            if existing is not None:
                return (True, str(existing.memory_id))
            return (False, None)

        except Exception as e:
            logger.log_warning(
                "duplicate_check_failed",
                {"content_hash": content_hash, "error": str(e)}
            )
            return (False, None)
    
    async def _extract_content_metadata(
        self,
        request: IngestionRequest
    ) -> ExtractedContent:
        """Extract metadata and key information from content."""
        
        try:
            # Basic extraction (Level 2 will implement LLM-based extraction)
            content = request.content
            
            # Extract title (first line or first sentence)
            title = self._extract_title(content, request.content_type)
            
            # Generate summary
            summary = self._generate_summary(content)
            
            # Extract key points
            key_points = self._extract_key_points(content)
            
            # Extract entities (simplified)
            entities = self._extract_entities(content)
            
            # Extract topics
            topics = self._extract_topics(content, request.source)
            
            # Detect language (simplified)
            language = self._detect_language(content)
            
            # Calculate confidence score
            confidence_score = self._calculate_confidence(content, request.content_type)
            
            return ExtractedContent(
                title=title,
                summary=summary,
                key_points=key_points,
                entities=entities,
                topics=topics,
                language=language,
                confidence_score=confidence_score
            )
            
        except Exception as e:
            logger.log_warning(
                "metadata_extraction_failed",
                {"error": str(e), "source": request.source}
            )
            
            # Return minimal extraction
            return ExtractedContent(
                summary=request.content[:200] + "..." if len(request.content) > 200 else request.content,
                confidence_score=0.5
            )

    def _extract_title(self, content: str, content_type: ContentType) -> Optional[str]:
        """Extract title from content based on type."""

        if content_type == ContentType.MARKDOWN:
            # Look for markdown headers
            match = re.search(r'^#\s+(.+)$', content, re.MULTILINE)
            if match:
                return match.group(1).strip()

        elif content_type == ContentType.HTML:
            # Look for HTML title tags
            match = re.search(r'<title[^>]*>([^<]+)</title>', content, re.IGNORECASE)
            if match:
                return match.group(1).strip()

        elif content_type == ContentType.CODE:
            # Look for file headers or class names
            match = re.search(r'(?:class|function|def)\s+(\w+)', content)
            if match:
                return f"Code: {match.group(1)}"

        # Default: use first line or sentence
        lines = content.strip().split('\n')
        if lines:
            first_line = lines[0].strip()
            if len(first_line) < 100:
                return first_line

        # Use first sentence
        sentences = re.split(r'[.!?]+', content)
        if sentences:
            first_sentence = sentences[0].strip()
            if len(first_sentence) < 100:
                return first_sentence

        return None

    def _generate_summary(self, content: str) -> str:
        """Generate summary of content."""

        # Simple extractive summary (Level 2 will use LLM)
        sentences = re.split(r'[.!?]+', content)

        # Take first few sentences up to 200 characters
        summary_parts = []
        total_length = 0

        for sentence in sentences[:5]:  # Max 5 sentences
            sentence = sentence.strip()
            if not sentence:
                continue

            if total_length + len(sentence) > 200:
                break

            summary_parts.append(sentence)
            total_length += len(sentence)

        summary = '. '.join(summary_parts)
        if summary and not summary.endswith('.'):
            summary += '.'

        return summary or content[:200] + "..." if len(content) > 200 else content

    def _extract_key_points(self, content: str) -> List[str]:
        """Extract key points from content."""

        key_points = []

        # Look for bullet points
        bullet_matches = re.findall(r'^\s*[-*•]\s+(.+)$', content, re.MULTILINE)
        key_points.extend([point.strip() for point in bullet_matches[:5]])

        # Look for numbered lists
        numbered_matches = re.findall(r'^\s*\d+\.\s+(.+)$', content, re.MULTILINE)
        key_points.extend([point.strip() for point in numbered_matches[:5]])

        # Look for sentences with keywords
        important_sentences = re.findall(
            r'[^.!?]*(?:important|key|critical|essential|main|primary)[^.!?]*[.!?]',
            content,
            re.IGNORECASE
        )
        key_points.extend([sent.strip() for sent in important_sentences[:3]])

        return key_points[:10]  # Limit to 10 key points

    def _extract_entities(self, content: str) -> List[str]:
        """Extract entities from content (simplified)."""

        entities = []

        # Extract capitalized words (potential proper nouns)
        capitalized = re.findall(r'\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\b', content)
        entities.extend(list(set(capitalized))[:10])

        # Extract email addresses
        emails = re.findall(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', content)
        entities.extend(emails)

        # Extract URLs
        urls = re.findall(r'https?://[^\s]+', content)
        entities.extend(urls)

        # Extract dates
        dates = re.findall(r'\b\d{4}-\d{2}-\d{2}\b|\b\d{1,2}/\d{1,2}/\d{4}\b', content)
        entities.extend(dates)

        return list(set(entities))[:20]  # Limit and deduplicate

    def _extract_topics(self, content: str, source: ContentSource) -> List[str]:
        """Extract topics from content."""

        topics = []

        # Add source-based topic
        topics.append(source.value)

        # Look for hashtags
        hashtags = re.findall(r'#(\w+)', content)
        topics.extend(hashtags)

        # Look for common technical terms
        tech_terms = [
            'api', 'database', 'server', 'client', 'authentication', 'authorization',
            'security', 'performance', 'optimization', 'deployment', 'testing',
            'documentation', 'configuration', 'monitoring', 'logging', 'error'
        ]

        content_lower = content.lower()
        for term in tech_terms:
            if term in content_lower:
                topics.append(term)

        return list(set(topics))[:10]  # Limit and deduplicate

    def _detect_language(self, content: str) -> str:
        """Detect content language (simplified)."""

        # Simple heuristic based on common words
        english_words = ['the', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by']

        content_lower = content.lower()
        english_count = sum(1 for word in english_words if word in content_lower)

        # If we find several English words, assume English
        if english_count >= 3:
            return "en"

        # Default to English
        return "en"

    def _calculate_confidence(self, content: str, content_type: ContentType) -> float:
        """Calculate confidence score for extraction quality."""

        confidence = 1.0

        # Reduce confidence for very short content
        if len(content) < 50:
            confidence *= 0.7

        # Reduce confidence for very long content (harder to process)
        if len(content) > 50000:
            confidence *= 0.8

        # Adjust based on content type
        if content_type == ContentType.CODE:
            confidence *= 0.9  # Code is harder to extract metadata from
        elif content_type == ContentType.JSON:
            confidence *= 0.8  # Structured data
        elif content_type == ContentType.TEXT:
            confidence *= 1.0  # Best for text processing

        return max(0.1, min(1.0, confidence))

    async def _generate_embeddings(
        self,
        content: str,
        summary: str
    ) -> Dict[str, List[float]]:
        """Generate embeddings for content and summary."""

        if not self.embedding_service_available:
            # Mock embeddings for Level 1
            return await self._mock_generate_embeddings(content, summary)

        # Level 2: Actual embedding service
        # return await self.embedding_service.generate_embeddings(content, summary)
        return await self._mock_generate_embeddings(content, summary)

    async def _mock_generate_embeddings(
        self,
        content: str,
        summary: str
    ) -> Dict[str, List[float]]:
        """Generate mock embeddings for testing."""

        # Simulate processing time
        await asyncio.sleep(0.1)

        # Generate deterministic mock embeddings based on content hash
        content_hash = hashlib.md5(content.encode()).hexdigest()
        summary_hash = hashlib.md5(summary.encode()).hexdigest()

        # Convert hash to float values
        content_embedding = [
            (int(content_hash[i:i+2], 16) - 128) / 128.0
            for i in range(0, min(len(content_hash), self.embedding_dimensions * 2), 2)
        ]

        summary_embedding = [
            (int(summary_hash[i:i+2], 16) - 128) / 128.0
            for i in range(0, min(len(summary_hash), self.embedding_dimensions * 2), 2)
        ]

        # Pad to required dimensions
        while len(content_embedding) < self.embedding_dimensions:
            content_embedding.append(0.0)
        while len(summary_embedding) < self.embedding_dimensions:
            summary_embedding.append(0.0)

        # Truncate to required dimensions
        content_embedding = content_embedding[:self.embedding_dimensions]
        summary_embedding = summary_embedding[:self.embedding_dimensions]

        return {
            "content": content_embedding,
            "summary": summary_embedding
        }

    async def _store_processed_content(
        self,
        request: IngestionRequest,
        extracted: ExtractedContent,
        embeddings: Dict[str, List[float]],
        content_hash: str
    ) -> str:
        """Store processed content in appropriate memory systems."""

        # Generate UUID object (not string) for database
        memory_id_uuid = uuid.uuid4()
        memory_id = str(memory_id_uuid)

        # Prepare metadata as a dict (MemoryMetadata class doesn't exist)
        metadata = {
            "tags": extracted.topics + [request.source.value, request.content_type.value],
            "source": f"scribe_{request.source.value}",
            "confidence_score": extracted.confidence_score,
            "additional_metadata": {
                "title": extracted.title,
                "key_points": extracted.key_points,
                "entities": extracted.entities,
                "language": extracted.language,
                "content_type": request.content_type.value,
                "priority": request.priority,
                "embeddings": {
                    "content_dimensions": len(embeddings["content"]),
                    "summary_dimensions": len(embeddings["summary"]),
                    "model": self.embedding_model
                },
                **(request.metadata or {})
            }
        }

        # Create memory record matching the database schema
        memory_record = MemoryRecord(
            memory_id=memory_id_uuid,  # Fixed: use UUID object, not string
            agent_id=request.agent_id or "scribe",  # Fixed: provide default value for NOT NULL constraint
            tenant_id=request.tenant_id or "default",
            source_type=map_content_source_to_db_type(request.source),  # Fixed: map to DB allowed values
            content_text=request.content,  # Maps to content_text column
            content_hash=content_hash,
            memory_metadata={  # Maps to metadata column (renamed to memory_metadata in model)
                "original_content": request.content,
                "extracted_summary": extracted.summary,
                "extracted_metadata": extracted.model_dump(),  # Fixed: Pydantic v2 compatibility
                "embeddings": embeddings,
                "tags": metadata["tags"],  # Fixed: metadata is now a dict
                "source": metadata["source"],
                "confidence_score": metadata["confidence_score"],
                "additional_metadata": metadata["additional_metadata"]
            }
        )

        # Store in database
        self.db.add(memory_record)
        self.db.commit()
        self.db.refresh(memory_record)

        # Store in appropriate memory systems via coordinator
        # Make this non-fatal - if delegation fails, content is still stored in DB
        try:
            await self._delegate_to_memory_systems(memory_record, request)
        except Exception as e:
            logger.log_warning(
                "memory_delegation_failed_non_fatal",
                {
                    "memory_id": memory_id,
                    "error": str(e),
                    "error_type": type(e).__name__
                }
            )
            # Continue anyway - the content is already stored in the database

        logger.log_info(
            "content_stored",
            {
                "memory_id": memory_id,
                "content_hash": content_hash,
                "source_type": memory_record.source_type,  # Fixed: use source_type instead of memory_type
                "tenant_id": memory_record.tenant_id
            }
        )

        return memory_id

    def _determine_memory_type(self, request: IngestionRequest) -> MemoryType:
        """Determine appropriate memory type based on content source and priority."""

        # High priority or execution results go to working memory (both stores)
        if request.priority >= 8 or request.source == ContentSource.EXECUTION_RESULT:
            return MemoryType.WORKING

        # Interactive content goes to short-term first
        if request.source in [ContentSource.USER_INPUT, ContentSource.CONVERSATION]:
            return MemoryType.SHORT_TERM

        # Documentation and external content go to long-term
        if request.source in [ContentSource.DOCUMENTATION, ContentSource.EXTERNAL_API, ContentSource.WEB_SCRAPE]:
            return MemoryType.LONG_TERM

        # Default to long-term for persistence
        return MemoryType.LONG_TERM

    async def _delegate_to_memory_systems(
        self,
        memory_record: MemoryRecord,
        request: IngestionRequest
    ) -> None:
        """Delegate storage to appropriate memory systems via coordinator."""

        try:
            # Determine memory type from request
            memory_type = self._determine_memory_type(request)

            # Create memory request for coordinator
            memory_request = MemoryRequest(
                operation=MemoryOperation.STORE,
                memory_type=memory_type,
                memory_id=str(memory_record.memory_id),
                value=memory_record.memory_metadata,  # Use memory_metadata instead of value
                metadata=memory_record.memory_metadata if isinstance(memory_record.memory_metadata, dict) else {},
                tenant_id=memory_record.tenant_id,
                agent_id=memory_record.agent_id
            )

            # Delegate to coordinator
            result = await self.coordinator.handle_memory_request(memory_request)

            if not result.success:
                logger.log_warning(
                    "memory_delegation_failed",
                    {
                        "memory_id": memory_record.memory_id,
                        "error": result.error
                    }
                )

        except Exception as e:
            logger.log_error(
                "memory_delegation_error",
                {
                    "memory_id": memory_record.memory_id,
                    "error": str(e)
                }
            )

    # Utility methods for content analysis

    async def analyze_content_quality(self, content: str) -> Dict[str, Any]:
        """Analyze content quality metrics."""

        return {
            "length": len(content),
            "word_count": len(content.split()),
            "sentence_count": len(re.split(r'[.!?]+', content)),
            "paragraph_count": len([p for p in content.split('\n\n') if p.strip()]),
            "readability_score": self._calculate_readability(content),
            "information_density": self._calculate_information_density(content)
        }

    def _calculate_readability(self, content: str) -> float:
        """Calculate simple readability score."""

        words = content.split()
        sentences = re.split(r'[.!?]+', content)

        if not sentences or not words:
            return 0.0

        avg_sentence_length = len(words) / len(sentences)

        # Simple readability score (lower is better)
        score = max(0.0, min(1.0, 1.0 - (avg_sentence_length - 15) / 50))
        return score

    def _calculate_information_density(self, content: str) -> float:
        """Calculate information density score."""

        # Count unique words vs total words
        words = re.findall(r'\b\w+\b', content.lower())
        if not words:
            return 0.0

        unique_words = set(words)
        density = len(unique_words) / len(words)

        return min(1.0, density * 2)  # Scale to 0-1 range
