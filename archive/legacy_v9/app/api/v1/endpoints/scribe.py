"""
Memory Scribe API Endpoints - Level 1 Component

API endpoints for the Memory Scribe Agent.
Provides content ingestion and processing capabilities.

Part of DRYAD.AI Agent Evolution Architecture Level 1.
"""

from typing import Dict, Any, Optional, List
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field

from app.database.database import get_db
from app.services.memory_guild.scribe import (
    MemoryScribeAgent, IngestionRequest, IngestionResult,
    ContentSource, ContentType
)
from app.services.memory_guild.coordinator import MemoryCoordinatorAgent
from app.services.logging.logger import StructuredLogger
from app.core.security import get_current_user

router = APIRouter(prefix="/scribe", tags=["scribe"])
logger = StructuredLogger("scribe_api")


# API Schemas
class ContentIngestionRequest(BaseModel):
    """Schema for content ingestion."""
    content: str = Field(..., description="Raw content to ingest")
    source: ContentSource = Field(..., description="Source of the content")
    content_type: ContentType = Field(ContentType.TEXT, description="Type of content")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Additional metadata")
    priority: int = Field(5, description="Processing priority (1-10)")
    deduplicate: bool = Field(True, description="Enable deduplication")


class BatchIngestionRequest(BaseModel):
    """Schema for batch content ingestion."""
    items: List[ContentIngestionRequest] = Field(..., description="List of content items to ingest")


class ContentAnalysisRequest(BaseModel):
    """Schema for content analysis."""
    content: str = Field(..., description="Content to analyze")


class ContentAnalysisResponse(BaseModel):
    """Schema for content analysis response."""
    quality_metrics: Dict[str, Any]
    extracted_metadata: Dict[str, Any]
    recommendations: List[str]


@router.post("/ingest", response_model=IngestionResult)
async def ingest_content(
    request: ContentIngestionRequest,
    db: Session = Depends(get_db),
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Ingest content into the Memory Guild.
    
    Processes raw content through the complete ingestion pipeline:
    - Metadata extraction
    - Deduplication
    - Embedding generation
    - Storage in appropriate memory systems
    """
    try:
        coordinator = MemoryCoordinatorAgent(db)
        scribe = MemoryScribeAgent(db, coordinator)
        
        ingestion_request = IngestionRequest(
            content=request.content,
            source=request.source,
            content_type=request.content_type,
            metadata=request.metadata,
            tenant_id=current_user.get("tenant_id", "default"),
            agent_id=current_user.get("agent_id"),
            priority=request.priority,
            deduplicate=request.deduplicate
        )
        
        logger.log_info(
            "content_ingestion_request",
            {
                "source": request.source,
                "content_type": request.content_type,
                "content_length": len(request.content),
                "priority": request.priority,
                "user_id": current_user.get("user_id"),
                "tenant_id": current_user.get("tenant_id")
            }
        )
        
        result = await scribe.ingest_content(ingestion_request)
        return result
        
    except ValueError as e:
        logger.log_warning(
            "content_ingestion_validation_error",
            {"error": str(e), "source": request.source}
        )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.log_error(
            "content_ingestion_error",
            {"error": str(e), "source": request.source}
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to ingest content"
        )


@router.post("/ingest/batch", response_model=List[IngestionResult])
async def ingest_batch(
    request: BatchIngestionRequest,
    db: Session = Depends(get_db),
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Ingest multiple content items in batch.
    
    Processes multiple content items efficiently with parallel processing.
    """
    try:
        coordinator = MemoryCoordinatorAgent(db)
        scribe = MemoryScribeAgent(db, coordinator)
        
        # Convert to internal format
        ingestion_requests = []
        for item in request.items:
            ingestion_requests.append(IngestionRequest(
                content=item.content,
                source=item.source,
                content_type=item.content_type,
                metadata=item.metadata,
                tenant_id=current_user.get("tenant_id", "default"),
                agent_id=current_user.get("agent_id"),
                priority=item.priority,
                deduplicate=item.deduplicate
            ))
        
        logger.log_info(
            "batch_ingestion_request",
            {
                "batch_size": len(request.items),
                "user_id": current_user.get("user_id"),
                "tenant_id": current_user.get("tenant_id")
            }
        )
        
        results = await scribe.ingest_batch(ingestion_requests)
        return results
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.log_error(
            "batch_ingestion_error",
            {"error": str(e), "batch_size": len(request.items)}
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to ingest batch content"
        )


@router.post("/ingest/file")
async def ingest_file(
    file: UploadFile = File(...),
    source: ContentSource = ContentSource.FILE_UPLOAD,
    priority: int = 5,
    deduplicate: bool = True,
    db: Session = Depends(get_db),
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Ingest content from uploaded file.
    
    Supports text files, documents, and other readable formats.
    """
    try:
        # Read file content
        content = await file.read()
        
        # Determine content type from file extension
        filename = file.filename or "unknown"
        if filename.endswith('.md'):
            content_type = ContentType.MARKDOWN
        elif filename.endswith('.html'):
            content_type = ContentType.HTML
        elif filename.endswith('.json'):
            content_type = ContentType.JSON
        elif filename.endswith('.csv'):
            content_type = ContentType.CSV
        elif filename.endswith(('.py', '.js', '.java', '.cpp', '.c')):
            content_type = ContentType.CODE
        else:
            content_type = ContentType.TEXT
        
        # Decode content
        try:
            text_content = content.decode('utf-8')
        except UnicodeDecodeError:
            raise ValueError("File must be text-based and UTF-8 encoded")
        
        coordinator = MemoryCoordinatorAgent(db)
        scribe = MemoryScribeAgent(db, coordinator)
        
        ingestion_request = IngestionRequest(
            content=text_content,
            source=source,
            content_type=content_type,
            metadata={
                "filename": filename,
                "file_size": len(content),
                "content_type": file.content_type
            },
            tenant_id=current_user.get("tenant_id", "default"),
            agent_id=current_user.get("agent_id"),
            priority=priority,
            deduplicate=deduplicate
        )
        
        logger.log_info(
            "file_ingestion_request",
            {
                "filename": filename,
                "file_size": len(content),
                "content_type": content_type,
                "user_id": current_user.get("user_id")
            }
        )
        
        result = await scribe.ingest_content(ingestion_request)
        return result
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.log_error(
            "file_ingestion_error",
            {"error": str(e), "filename": file.filename}
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to ingest file content"
        )


@router.post("/analyze", response_model=ContentAnalysisResponse)
async def analyze_content(
    request: ContentAnalysisRequest,
    db: Session = Depends(get_db),
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Analyze content quality and extract metadata without storing.
    
    Provides content analysis for preview before ingestion.
    """
    try:
        coordinator = MemoryCoordinatorAgent(db)
        scribe = MemoryScribeAgent(db, coordinator)
        
        # Analyze content quality
        quality_metrics = await scribe.analyze_content_quality(request.content)
        
        # Extract metadata (without storing)
        ingestion_request = IngestionRequest(
            content=request.content,
            source=ContentSource.USER_INPUT,
            content_type=ContentType.TEXT,
            tenant_id=current_user.get("tenant_id", "default"),
            agent_id=current_user.get("agent_id")
        )
        
        extracted = await scribe._extract_content_metadata(ingestion_request)
        
        # Generate recommendations
        recommendations = []
        
        if quality_metrics["length"] < 50:
            recommendations.append("Content is very short - consider adding more detail")
        elif quality_metrics["length"] > 50000:
            recommendations.append("Content is very long - consider breaking into smaller pieces")
        
        if quality_metrics["readability_score"] < 0.3:
            recommendations.append("Content may be difficult to read - consider shorter sentences")
        
        if quality_metrics["information_density"] < 0.2:
            recommendations.append("Content has low information density - consider removing repetition")
        
        if not extracted.title:
            recommendations.append("Consider adding a clear title or heading")
        
        if len(extracted.key_points) == 0:
            recommendations.append("Consider adding bullet points or key takeaways")
        
        logger.log_info(
            "content_analysis_completed",
            {
                "content_length": quality_metrics["length"],
                "word_count": quality_metrics["word_count"],
                "recommendations_count": len(recommendations),
                "user_id": current_user.get("user_id")
            }
        )
        
        return ContentAnalysisResponse(
            quality_metrics=quality_metrics,
            extracted_metadata=extracted.dict(),
            recommendations=recommendations
        )
        
    except Exception as e:
        logger.log_error(
            "content_analysis_error",
            {"error": str(e), "content_length": len(request.content)}
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to analyze content"
        )


@router.get("/stats")
async def get_ingestion_stats(
    db: Session = Depends(get_db),
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Get ingestion statistics for the current tenant.
    
    Returns metrics about content ingestion activity.
    """
    try:
        from app.services.memory_guild.models import MemoryRecord
        
        tenant_id = current_user.get("tenant_id", "default")
        
        # Get basic statistics
        total_memories = db.query(MemoryRecord).filter(
            MemoryRecord.tenant_id == tenant_id
        ).count()
        
        # Get statistics by source
        source_stats = {}
        for source in ContentSource:
            count = db.query(MemoryRecord).filter(
                MemoryRecord.tenant_id == tenant_id,
                MemoryRecord.metadata.has(
                    MemoryRecord.metadata.additional_metadata.contains({"source": f"scribe_{source.value}"})
                )
            ).count()
            source_stats[source.value] = count
        
        return {
            "tenant_id": tenant_id,
            "total_memories": total_memories,
            "source_breakdown": source_stats,
            "scribe_available": True,
            "embedding_service_available": False  # Level 1 limitation
        }
        
    except Exception as e:
        logger.log_error(
            "ingestion_stats_error",
            {"error": str(e), "tenant_id": current_user.get("tenant_id")}
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get ingestion statistics"
        )
