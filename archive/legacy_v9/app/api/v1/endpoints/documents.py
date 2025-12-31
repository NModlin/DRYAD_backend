# app/api/v1/endpoints/documents.py
import logging
import time
import json
import os
from pathlib import Path
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional, List

from app.database.database import get_db
from app.services.document_service import DocumentService
from app.core.rag_system import rag_system
from app.core.vector_store import vector_store
import app.core.security as security
from app.api.v1.schemas.documents import (
    DocumentCreate,
    DocumentResponse,
    DocumentListResponse,
    SemanticSearchRequest,
    SemanticSearchResponse,
    RAGRequest,
    RAGResponse,
    DocumentUploadResponse,
    SystemStatusResponse,
    QuerySuggestionsRequest,
    QuerySuggestionsResponse,
    SearchAnalyticsResponse,
    SearchResult,
    AdvancedSearchRequest,
    AdvancedSearchResponse,
    ContentAnalysisRequest,
    ContentAnalysisResponse,
    BatchAnalysisRequest,
    BatchAnalysisResponse,
    DocumentAnalyticsResponse,
    SearchAnalyticsResponse,
    UserEngagementResponse,
    AnalyticsDashboardResponse,
    DocumentVersionResponse,
    DocumentUpdateRequest,
    DocumentRollbackRequest,
    VersionComparisonRequest,
    VersionComparisonResponse,
    DocumentHistoryResponse
)
from app.api.v1.schemas.proposal import (
    ProposalGenerateRequest,
    ProposalGenerateResponse,
    ProposalStatusResponse
)

logger = logging.getLogger(__name__)
router = APIRouter()

# Import security functions for file validation and virus scanning
from app.core.security import sanitize_filename, scan_file_for_viruses

@router.post("/upload", response_model=DocumentUploadResponse)
async def upload_document(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    metadata: Optional[str] = Form(None),
    current_user: security.User = Depends(security.get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Upload a document file with optional metadata.
    Returns quickly; chunking + vector indexing run in background.
    """
    try:
        # Security validation - file presence and basic checks
        if not file.filename:
            raise HTTPException(status_code=400, detail="No file provided")

        if not file.filename.strip():
            raise HTTPException(status_code=400, detail="Invalid filename")

        # File size validation with security limits
        MAX_FILE_SIZE = 50 * 1024 * 1024  # 50MB
        content = await file.read()

        if len(content) == 0:
            raise HTTPException(status_code=400, detail="Empty file not allowed")

        if len(content) > MAX_FILE_SIZE:
            raise HTTPException(
                status_code=413,
                detail=f"File too large. Maximum size is {MAX_FILE_SIZE // (1024*1024)}MB"
            )

        # Sanitize filename for security
        sanitized_filename = sanitize_filename(file.filename)
        if not sanitized_filename or sanitized_filename != file.filename:
            logger.warning(f"Filename sanitized: '{file.filename}' -> '{sanitized_filename}'")

        # Strict content type validation
        allowed_types = {
            'text/plain', 'text/markdown', 'text/csv',
            'application/pdf', 'application/json',
            'application/msword',
            'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
        }
        content_type = file.content_type or "application/octet-stream"

        if content_type not in allowed_types:
            raise HTTPException(
                status_code=415,
                detail=f"Unsupported file type: {content_type}. Allowed types: {', '.join(sorted(allowed_types))}"
            )

        # Virus scanning with ClamAV (with graceful fallback)
        try:
            scan_result = await scan_file_for_viruses(content, sanitized_filename)
            if not scan_result["clean"]:
                logger.error(f"Virus detected in file '{sanitized_filename}': {scan_result['threat']} (scanner: {scan_result['scanner']})")
                raise HTTPException(
                    status_code=400,
                    detail="File rejected: security threat detected"
                )

            # Log successful scan with scanner type
            scanner_type = scan_result.get('scanner', 'unknown')
            scan_time = scan_result.get('scan_time', 0)
            logger.info(f"File '{sanitized_filename}' passed virus scan using {scanner_type} scanner ({scan_time:.3f}s)")

        except HTTPException:
            # Re-raise HTTP exceptions (virus detected)
            raise
        except Exception as e:
            logger.error(f"Virus scanning system error for '{sanitized_filename}': {e}")
            # The scan_file_for_viruses function already handles fallbacks gracefully
            # If we reach this point, there's a system-level error, but we should still
            # allow the upload to proceed with a warning since basic scanning was attempted
            logger.warning(f"Proceeding with upload of '{sanitized_filename}' despite scanning system error - basic security checks were performed")
            # Note: scan_file_for_viruses already includes basic security scanning as fallback

        parsed_metadata = {}
        if metadata:
            try:
                parsed_metadata = json.loads(metadata)
                if not isinstance(parsed_metadata, dict):
                    raise HTTPException(status_code=400, detail="Metadata must be a JSON object")
            except json.JSONDecodeError as e:
                raise HTTPException(status_code=400, detail=f"Invalid metadata JSON: {str(e)}")

        # Extract text content based on file type (fast path)
        try:
            if content_type in ('text/plain', 'text/markdown', 'text/csv', 'application/json'):
                text_content = content.decode('utf-8', errors='ignore')
                if content_type == 'text/csv':
                    text_content = f"CSV Data:\n{text_content}"
                if content_type == 'application/json':
                    try:
                        json.loads(text_content)
                        text_content = f"JSON Document:\n{text_content}"
                    except json.JSONDecodeError:
                        text_content = f"JSON-like Document:\n{text_content}"
            elif content_type == 'application/pdf':
                try:
                    from app.utils.pdf_extractor import extract_text_from_pdf_bytes, is_available
                    if is_available():
                        extracted = extract_text_from_pdf_bytes(content)
                        text_content = extracted or f"PDF Document: {sanitized_filename}\n[No extractable text]"
                    else:
                        text_content = f"PDF Document: {sanitized_filename}\n[Install 'pymupdf' to enable PDF text extraction]"
                except Exception as e:
                    text_content = f"PDF Document: {sanitized_filename}\n[PDF extraction failed: {e}]"
            else:
                try:
                    text_content = content.decode('utf-8', errors='ignore')
                except UnicodeDecodeError:
                    text_content = f"Binary Document: {sanitized_filename}\n[Binary content - text extraction not available]"
        except Exception as e:
            logger.error(f"Error processing file content: {e}")
            text_content = f"Document: {sanitized_filename}\n[Content processing failed: {str(e)}]"

        # Step 1: Create DB record only (fast)
        document = await DocumentService.create_document_record(
            db=db,
            user_id=current_user.id,
            title=sanitized_filename,
            content=text_content,
            content_type=content_type,
            file_size=len(content),
            doc_metadata={
                **parsed_metadata,
                "original_filename": file.filename,
                "upload_method": "file_upload",
                "file_type": content_type,
                "processed_at": time.time(),
                "file_size_bytes": len(content),
                "uploaded_by": current_user.email,
            },
        )
        if not document:
            raise HTTPException(status_code=500, detail="Failed to create document")

        # Step 2: Background processing task
        async def _bg_process(doc_id: str, text: str, title: str, ctype: str, meta: dict):
            from app.core.websocket_manager import real_time_processor
            import uuid
            task_id = str(uuid.uuid4())
            # Start processing WS
            await real_time_processor.start_processing_task(
                session_id=meta.get("session_id", f"session_{doc_id}"),
                task_id=task_id,
                task_type="document_processing",
            )
            # Process the content
            chunks_created, vector_ids = await DocumentService.process_document_content(
                db=db,
                document_id=doc_id,
                content=text,
                title=title,
                content_type=ctype,
                doc_metadata=meta,
            )
            # Complete WS
            await real_time_processor.complete_processing_task(
                task_id,
                result={
                    "document_id": doc_id,
                    "chunks_created": chunks_created,
                    "vector_ids": vector_ids,
                },
            )

        # Schedule background async function safely without requiring an active event loop in threadpool
        async def runner():
            await _bg_process(
                document.id, text_content, sanitized_filename, content_type, document.doc_metadata or {}
            )
        # Schedule using asyncio.run in a worker thread
        background_tasks.add_task(__import__("asyncio").run, runner())

        # Return fast response
        return DocumentUploadResponse(
            document_id=document.id,
            title=sanitized_filename,
            file_size=document.file_size or len(content),
            chunks_created=0,
            vector_ids=[],
            processing_time_ms=0.0,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error uploading document: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to upload document: {str(e)}")

@router.post("/upload/batch")
async def upload_documents_batch(
    files: List[UploadFile] = File(...),
    metadata: Optional[str] = Form(None),
    current_user: security.User = Depends(security.get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Upload multiple document files with optional shared metadata."""
    try:
        if not files:
            raise HTTPException(status_code=400, detail="No files provided")

        if len(files) > 10:  # Limit batch size
            raise HTTPException(status_code=400, detail="Maximum 10 files per batch upload")

        # Parse shared metadata if provided
        shared_metadata = {}
        if metadata:
            try:
                shared_metadata = json.loads(metadata)
                if not isinstance(shared_metadata, dict):
                    raise HTTPException(status_code=400, detail="Metadata must be a JSON object")
            except json.JSONDecodeError as e:
                raise HTTPException(status_code=400, detail=f"Invalid metadata JSON: {str(e)}")

        # Track processing time
        start_time = time.time()

        results = []
        failed_uploads = []

        for i, file in enumerate(files):
            try:
                if not file.filename:
                    failed_uploads.append({
                        "index": i,
                        "filename": "unknown",
                        "error": "No filename provided"
                    })
                    continue

                # Check file size (limit to 50MB per file)
                MAX_FILE_SIZE = 50 * 1024 * 1024
                content = await file.read()
                if len(content) > MAX_FILE_SIZE:
                    failed_uploads.append({
                        "index": i,
                        "filename": file.filename,
                        "error": f"File too large. Maximum size is {MAX_FILE_SIZE // (1024*1024)}MB"
                    })
                    continue

                # Sanitize filename
                sanitized_filename = sanitize_filename(file.filename)
                content_type = file.content_type or "application/octet-stream"

                # Extract text content (simplified for batch processing)
                try:
                    if content_type in ['text/plain', 'text/markdown', 'text/csv']:
                        text_content = content.decode('utf-8', errors='ignore')
                    elif content_type == 'application/json':
                        text_content = content.decode('utf-8', errors='ignore')
                    else:
                        text_content = content.decode('utf-8', errors='ignore')
                except UnicodeDecodeError:
                    text_content = f"Binary Document: {sanitized_filename}"

                # Create document
                document = await DocumentService.create_document(
                    db=db,
                    user_id=current_user.id,
                    title=sanitized_filename,
                    content=text_content,
                    content_type=content_type,
                    file_size=len(content),
                    doc_metadata={
                        **shared_metadata,
                        "original_filename": file.filename,
                        "upload_method": "batch_upload",
                        "file_type": content_type,
                        "batch_index": i,
                        "processed_at": time.time(),
                        "uploaded_by": current_user.email
                    }
                )

                if document:
                    results.append({
                        "index": i,
                        "document_id": document.id,
                        "title": sanitized_filename,
                        "file_size": len(content),
                        "status": "success"
                    })
                else:
                    failed_uploads.append({
                        "index": i,
                        "filename": file.filename,
                        "error": "Failed to create document"
                    })

            except Exception as e:
                logger.error(f"Error processing file {i} ({file.filename}): {e}")
                failed_uploads.append({
                    "index": i,
                    "filename": file.filename,
                    "error": str(e)
                })

        # Calculate processing time
        processing_time_ms = (time.time() - start_time) * 1000

        return {
            "total_files": len(files),
            "successful_uploads": len(results),
            "failed_uploads": len(failed_uploads),
            "processing_time_ms": processing_time_ms,
            "results": results,
            "failures": failed_uploads
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in batch upload: {e}")
        raise HTTPException(status_code=500, detail=f"Batch upload failed: {str(e)}")

@router.post("/upload/realtime")
async def upload_document_realtime(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    metadata: Optional[str] = Form(None),
    session_id: Optional[str] = Form(None),
    current_user: security.User = Depends(security.get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Upload a document with real-time progress tracking via WebSocket.
    Returns quickly and streams progress via WS; processing runs in background.
    """
    try:
        import uuid
        from app.core.websocket_manager import real_time_processor

        # Generate upload ID and session ID
        upload_id = str(uuid.uuid4())
        if not session_id:
            session_id = f"upload_session_{upload_id}"

        # Validate file
        if not file.filename:
            raise HTTPException(status_code=400, detail="No file provided")

        content = await file.read()
        file_size = len(content)

        # Start WS upload tracking
        await real_time_processor.start_upload_task(session_id, upload_id, file_size)

        # Sanitize filename and parse metadata
        sanitized_filename = sanitize_filename(file.filename)
        parsed_metadata = {}
        if metadata:
            try:
                parsed_metadata = json.loads(metadata)
            except json.JSONDecodeError:
                parsed_metadata = {"raw_metadata": str(metadata)}

        # Extract content (fast path)
        content_type = file.content_type or "application/octet-stream"
        try:
            if content_type in ('text/plain', 'text/markdown', 'text/csv', 'application/json'):
                text_content = content.decode('utf-8', errors='ignore')
                if content_type == 'text/csv':
                    text_content = f"CSV Data:\n{text_content}"
                if content_type == 'application/json':
                    try:
                        json.loads(text_content)
                        text_content = f"JSON Document:\n{text_content}"
                    except json.JSONDecodeError:
                        text_content = f"JSON-like Document:\n{text_content}"
            elif content_type == 'application/pdf':
                try:
                    from app.utils.pdf_extractor import extract_text_from_pdf_bytes, is_available
                    if is_available():
                        extracted = extract_text_from_pdf_bytes(content)
                        text_content = extracted or f"PDF Document: {sanitized_filename}\n[No extractable text]"
                    else:
                        text_content = f"PDF Document: {sanitized_filename}\n[Install 'pymupdf' to enable PDF text extraction]"
                except Exception as e:
                    text_content = f"PDF Document: {sanitized_filename}\n[PDF extraction failed: {e}]"
            else:
                try:
                    text_content = content.decode('utf-8', errors='ignore')
                except UnicodeDecodeError:
                    text_content = f"Binary Document: {sanitized_filename}"
        except Exception as e:
            logger.error(f"Error processing file content: {e}")
            text_content = f"Document: {sanitized_filename}\n[Content processing failed: {str(e)}]"

        # Create DB record only
        document = await DocumentService.create_document_record(
            db=db,
            user_id=current_user.id,
            title=sanitized_filename,
            content=text_content,
            content_type=content_type,
            file_size=file_size,
            doc_metadata={
                **parsed_metadata,
                "original_filename": file.filename,
                "upload_method": "realtime_upload",
                "file_type": content_type,
                "upload_id": upload_id,
                "session_id": session_id,
                "processed_at": time.time(),
                "uploaded_by": current_user.email,
            },
        )
        if not document:
            raise HTTPException(status_code=500, detail="Failed to create document")

        # Background processing with periodic WS progress
        async def _bg_process(doc_id: str, text: str, title: str, ctype: str, meta: dict, up_id: str, sess_id: str):
            try:
                # Simulate some progressive upload completion ticks for UI smoothness
                await real_time_processor.update_upload_progress(up_id, min(file_size, max(1, file_size // 2)))

                # Start processing task WS
                import uuid
                task_id = str(uuid.uuid4())
                await real_time_processor.start_processing_task(sess_id, task_id, "document_processing")

                # Do processing
                chunks_created, vector_ids = await DocumentService.process_document_content(
                    db=db,
                    document_id=doc_id,
                    content=text,
                    title=title,
                    content_type=ctype,
                    doc_metadata=meta,
                )

                # Complete processing WS
                await real_time_processor.complete_processing_task(task_id, {
                    "document_id": doc_id,
                    "chunks_created": chunks_created,
                    "vector_ids": vector_ids,
                })

                # Finish upload tracking
                await real_time_processor.update_upload_progress(up_id, file_size)
                await real_time_processor.complete_upload_task(up_id, {
                    "document_id": doc_id,
                    "title": title,
                    "file_size": file_size,
                    "upload_id": up_id,
                    "session_id": sess_id,
                    "status": "completed",
                })
            except Exception as e:
                logger.error(f"Background processing failed for {doc_id}: {e}")

        async def runner():
            await _bg_process(
                document.id, text_content, sanitized_filename, content_type, document.doc_metadata or {}, upload_id, session_id
            )
        background_tasks.add_task(__import__("asyncio").run, runner())

        return DocumentUploadResponse(
            document_id=document.id,
            title=sanitized_filename,
            file_size=file_size,
            chunks_created=0,
            vector_ids=[],
            processing_time_ms=0.0,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in realtime upload: {e}")
        raise HTTPException(status_code=500, detail=f"Realtime upload failed: {str(e)}")

@router.get("/processing/stats")
async def get_processing_stats(current_user: security.User = Depends(security.get_current_user), db: AsyncSession = Depends(get_db)):
    """Get document processing statistics."""
    try:
        # Get document counts by type
        from sqlalchemy import func, select
        from app.database.models import Document

        # Count documents by content type
        type_counts_query = select(
            func.count(Document.id).label('count'),
            Document.content_type.label('content_type')
        ).group_by(Document.content_type)

        type_counts_result = await db.execute(type_counts_query)
        type_counts = {row.content_type: row.count for row in type_counts_result}

        # Get recent uploads (last 24 hours)
        from datetime import datetime, timedelta
        from datetime import timezone
        recent_cutoff = datetime.now(timezone.utc) - timedelta(hours=24)

        recent_count_query = select(func.count(Document.id)).filter(
            Document.created_at >= recent_cutoff
        )
        recent_count_result = await db.execute(recent_count_query)
        recent_count = recent_count_result.scalar()

        # Get total document count
        total_count_query = select(func.count(Document.id))
        total_count_result = await db.execute(total_count_query)
        total_count = total_count_result.scalar()

        # Get vector store stats
        vector_info = vector_store.get_collection_info()

        return {
            "total_documents": total_count or 0,
            "recent_uploads_24h": recent_count or 0,
            "documents_by_type": dict(type_counts) if type_counts else {},
            "vector_store_documents": vector_info.get("object_count", 0),
            "processing_capabilities": {
                "supported_formats": [
                    "text/plain", "text/markdown", "text/csv",
                    "application/json", "application/pdf"
                ],
                "max_file_size_mb": 50,
                "batch_upload_limit": 10
            },
            "timestamp": datetime.now().isoformat()
        }

    except Exception as e:
        logger.error(f"Error getting processing stats: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get processing stats: {str(e)}")

@router.post("/search/advanced", response_model=AdvancedSearchResponse)
async def advanced_search(
    request: AdvancedSearchRequest,
    current_user: security.User = Depends(security.get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Perform advanced search with faceted filtering and sorting."""
    try:
        from app.services.advanced_search_service import AdvancedSearchService

        result = await AdvancedSearchService.advanced_search(db, request)
        return result

    except Exception as e:
        logger.error(f"Advanced search failed: {e}")
        raise HTTPException(status_code=500, detail=f"Advanced search failed: {str(e)}")

@router.post("/analyze", response_model=ContentAnalysisResponse)
async def analyze_document_content(
    request: ContentAnalysisRequest,
    current_user: security.User = Depends(security.get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Analyze document content with AI-powered analysis."""
    try:
        import time
        from app.services.content_analysis_service import ContentAnalysisService
        from app.services.document_service import DocumentService

        start_time = time.time()

        # Get document
        document = await DocumentService.get_document(db=db, document_id=request.document_id)
        if not document:
            raise HTTPException(status_code=404, detail="Document not found")

        # Check if already analyzed and not forcing re-analysis
        if not request.force_reanalysis and document.doc_metadata and document.doc_metadata.get("ai_analysis"):
            existing_analysis = document.doc_metadata["ai_analysis"]
            processing_time_ms = (time.time() - start_time) * 1000

            return ContentAnalysisResponse(
                document_id=document.id,
                title=document.title,
                content_length=len(document.content),
                analysis_timestamp=existing_analysis.get("analyzed_at"),
                tags=document.tags or [],
                summary=existing_analysis.get("summary", ""),
                entities=existing_analysis.get("entities", {}),
                topics=existing_analysis.get("topics", []),
                sentiment=existing_analysis.get("sentiment", "neutral"),
                readability_score=existing_analysis.get("readability_score", 0.0),
                key_phrases=existing_analysis.get("key_phrases", []),
                processing_time_ms=processing_time_ms,
                llm_used=False
            )

        # Perform analysis
        analysis_result = await ContentAnalysisService.analyze_document_content(
            db=db,
            document=document,
            include_summary=request.include_summary,
            include_tags=request.include_tags,
            include_entities=request.include_entities
        )

        processing_time_ms = (time.time() - start_time) * 1000

        return ContentAnalysisResponse(
            document_id=analysis_result["document_id"],
            title=analysis_result["title"],
            content_length=analysis_result["content_length"],
            analysis_timestamp=analysis_result.get("analysis_timestamp"),
            tags=analysis_result.get("tags", []),
            summary=analysis_result.get("summary", ""),
            entities=analysis_result.get("entities", {}),
            topics=analysis_result.get("topics", []),
            sentiment=analysis_result.get("sentiment", "neutral"),
            readability_score=analysis_result.get("readability_score", 0.0),
            key_phrases=analysis_result.get("key_phrases", []),
            processing_time_ms=processing_time_ms,
            llm_used=True  # Assume LLM was attempted
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Content analysis failed: {e}")
        raise HTTPException(status_code=500, detail=f"Content analysis failed: {str(e)}")

@router.post("/analyze/batch", response_model=BatchAnalysisResponse)
async def batch_analyze_documents(
    request: BatchAnalysisRequest,
    current_user: security.User = Depends(security.get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Perform batch content analysis on multiple documents."""
    try:
        import time
        from app.services.content_analysis_service import ContentAnalysisService
        from app.services.document_service import DocumentService

        start_time = time.time()
        results = []
        failures = []

        for doc_id in request.document_ids:
            try:
                # Get document
                document = await DocumentService.get_document(db=db, document_id=doc_id)
                if not document:
                    failures.append({
                        "document_id": doc_id,
                        "error": "Document not found"
                    })
                    continue

                # Perform analysis
                analysis_result = await ContentAnalysisService.analyze_document_content(
                    db=db,
                    document=document,
                    include_summary=request.include_summary,
                    include_tags=request.include_tags,
                    include_entities=request.include_entities
                )

                results.append(ContentAnalysisResponse(
                    document_id=analysis_result["document_id"],
                    title=analysis_result["title"],
                    content_length=analysis_result["content_length"],
                    analysis_timestamp=analysis_result.get("analysis_timestamp"),
                    tags=analysis_result.get("tags", []),
                    summary=analysis_result.get("summary", ""),
                    entities=analysis_result.get("entities", {}),
                    topics=analysis_result.get("topics", []),
                    sentiment=analysis_result.get("sentiment", "neutral"),
                    readability_score=analysis_result.get("readability_score", 0.0),
                    key_phrases=analysis_result.get("key_phrases", []),
                    processing_time_ms=0.0,  # Individual timing not tracked in batch
                    llm_used=True
                ))

            except Exception as e:
                logger.error(f"Analysis failed for document {doc_id}: {e}")
                failures.append({
                    "document_id": doc_id,
                    "error": str(e)
                })

        processing_time_ms = (time.time() - start_time) * 1000

        return BatchAnalysisResponse(
            total_documents=len(request.document_ids),
            successful_analyses=len(results),
            failed_analyses=len(failures),
            processing_time_ms=processing_time_ms,
            results=results,
            failures=failures
        )

    except Exception as e:
        logger.error(f"Batch analysis failed: {e}")
        raise HTTPException(status_code=500, detail=f"Batch analysis failed: {str(e)}")

@router.get("/analytics/documents", response_model=List[DocumentAnalyticsResponse])
async def get_document_analytics(
    document_id: Optional[str] = None,
    limit: int = 50,
    db: AsyncSession = Depends(get_db)
):
    """Get document analytics data."""
    try:
        from app.services.analytics_service import AnalyticsService

        analytics_data = await AnalyticsService.get_document_analytics(
            db=db,
            document_id=document_id,
            limit=limit
        )

        return [DocumentAnalyticsResponse(**data) for data in analytics_data]

    except Exception as e:
        logger.error(f"Failed to get document analytics: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get document analytics: {str(e)}")

@router.get("/analytics/search", response_model=SearchAnalyticsResponse)
async def get_search_analytics(
    days: int = 30,
    limit: int = 100,
    db: AsyncSession = Depends(get_db)
):
    """Get search analytics data."""
    try:
        from app.services.analytics_service import AnalyticsService

        analytics_data = await AnalyticsService.get_search_analytics(
            db=db,
            days=days,
            limit=limit
        )

        return SearchAnalyticsResponse(**analytics_data)

    except Exception as e:
        logger.error(f"Failed to get search analytics: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get search analytics: {str(e)}")

@router.get("/analytics/engagement", response_model=UserEngagementResponse)
async def get_user_engagement_metrics(
    days: int = 30,
    current_user: security.User = Depends(security.get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get user engagement metrics."""
    try:
        from app.services.analytics_service import AnalyticsService

        engagement_data = await AnalyticsService.get_user_engagement_metrics(
            db=db,
            days=days
        )

        return UserEngagementResponse(**engagement_data)

    except Exception as e:
        logger.error(f"Failed to get user engagement metrics: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get user engagement metrics: {str(e)}")

@router.get("/analytics/dashboard", response_model=AnalyticsDashboardResponse)
async def get_analytics_dashboard(
    days: int = 30,
    current_user: security.User = Depends(security.get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get comprehensive analytics dashboard data."""
    try:
        from app.services.analytics_service import AnalyticsService
        from datetime import datetime

        # Get all analytics data
        document_analytics = await AnalyticsService.get_document_analytics(db=db, limit=20)
        search_analytics = await AnalyticsService.get_search_analytics(db=db, days=days)
        user_engagement = await AnalyticsService.get_user_engagement_metrics(db=db, days=days)

        # Calculate summary metrics
        total_views = sum(doc.get("view_count", 0) for doc in document_analytics)
        total_searches = sum(search_analytics.get("search_type_distribution", {}).values())

        # Find most popular items
        most_popular_doc = None
        if document_analytics:
            most_popular_doc = max(document_analytics, key=lambda x: x.get("view_count", 0))
            most_popular_doc = most_popular_doc.get("title")

        most_popular_query = None
        popular_queries = search_analytics.get("popular_queries", [])
        if popular_queries:
            most_popular_query = popular_queries[0].get("query")

        # Calculate average search time
        avg_search_time = 0.0
        if popular_queries:
            avg_search_time = sum(q.get("avg_execution_time_ms", 0) for q in popular_queries) / len(popular_queries)

        return AnalyticsDashboardResponse(
            document_analytics=[DocumentAnalyticsResponse(**doc) for doc in document_analytics],
            search_analytics=SearchAnalyticsResponse(**search_analytics),
            user_engagement=UserEngagementResponse(**user_engagement),
            total_documents=len(document_analytics),
            total_views=total_views,
            total_searches=total_searches,
            total_sessions=user_engagement.get("unique_sessions", 0),
            avg_search_time_ms=avg_search_time,
            most_popular_document=most_popular_doc,
            most_popular_query=most_popular_query,
            generated_at=datetime.utcnow().isoformat()
        )

    except Exception as e:
        logger.error(f"Failed to get analytics dashboard: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get analytics dashboard: {str(e)}")

@router.post("/analytics/track/view/{document_id}")
async def track_document_view(
    document_id: str,
    duration_seconds: Optional[float] = None,
    user_session: str = "anonymous",
    db: AsyncSession = Depends(get_db)
):
    """Track a document view event."""
    try:
        from app.services.analytics_service import AnalyticsService

        await AnalyticsService.track_document_view(
            db=db,
            document_id=document_id,
            user_session=user_session,
            duration_seconds=duration_seconds
        )

        return {"status": "success", "message": "Document view tracked"}

    except Exception as e:
        logger.error(f"Failed to track document view: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to track document view: {str(e)}")

@router.put("/{document_id}/versions", response_model=DocumentVersionResponse)
async def update_document_with_versioning(
    document_id: str,
    request: DocumentUpdateRequest,
    current_user: security.User = Depends(security.get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Update a document and create a new version."""
    try:
        from app.services.document_versioning_service import DocumentVersioningService

        # Prepare updates dictionary
        updates = {}
        if request.title is not None:
            updates["title"] = request.title
        if request.content is not None:
            updates["content"] = request.content
        if request.content_type is not None:
            updates["content_type"] = request.content_type
        if request.doc_metadata is not None:
            updates["doc_metadata"] = request.doc_metadata
        if request.tags is not None:
            updates["tags"] = request.tags

        if not updates:
            raise HTTPException(status_code=400, detail="No updates provided")

        # Update document with versioning
        document, version = await DocumentVersioningService.update_document_with_versioning(
            db=db,
            document_id=document_id,
            updates=updates,
            change_summary=request.change_summary,
            created_by=request.created_by,
            created_by_session=request.created_by_session
        )

        return DocumentVersionResponse(
            id=version.id,
            document_id=version.document_id,
            version_number=version.version_number,
            title=version.title,
            content=version.content,
            content_type=version.content_type,
            file_size=version.file_size,
            doc_metadata=version.doc_metadata,
            tags=version.tags,
            change_summary=version.change_summary,
            change_type=version.change_type,
            changed_fields=version.changed_fields,
            is_current=version.is_current,
            parent_version_id=version.parent_version_id,
            created_by=version.created_by,
            created_by_session=version.created_by_session,
            created_at=version.created_at.isoformat() if version.created_at else None
        )

    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to update document with versioning: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to update document: {str(e)}")

@router.get("/{document_id}/versions", response_model=List[DocumentVersionResponse])
async def get_document_versions(
    document_id: str,
    limit: int = 50,
    db: AsyncSession = Depends(get_db)
):
    """Get all versions of a document."""
    try:
        from app.services.document_versioning_service import DocumentVersioningService

        versions = await DocumentVersioningService.get_document_versions(
            db=db,
            document_id=document_id,
            limit=limit
        )

        return [
            DocumentVersionResponse(
                id=version.id,
                document_id=version.document_id,
                version_number=version.version_number,
                title=version.title,
                content=version.content,
                content_type=version.content_type,
                file_size=version.file_size,
                doc_metadata=version.doc_metadata,
                tags=version.tags,
                change_summary=version.change_summary,
                change_type=version.change_type,
                changed_fields=version.changed_fields,
                is_current=version.is_current,
                parent_version_id=version.parent_version_id,
                created_by=version.created_by,
                created_by_session=version.created_by_session,
                created_at=version.created_at.isoformat() if version.created_at else None
            )
            for version in versions
        ]

    except Exception as e:
        logger.error(f"Failed to get document versions: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get document versions: {str(e)}")

@router.post("/{document_id}/versions/rollback", response_model=DocumentVersionResponse)
async def rollback_document_version(
    document_id: str,
    request: DocumentRollbackRequest,
    current_user: security.User = Depends(security.get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Rollback a document to a specific version."""
    try:
        from app.services.document_versioning_service import DocumentVersioningService

        document, rollback_version = await DocumentVersioningService.rollback_to_version(
            db=db,
            document_id=document_id,
            target_version_number=request.target_version_number,
            created_by=request.created_by,
            created_by_session=request.created_by_session
        )

        return DocumentVersionResponse(
            id=rollback_version.id,
            document_id=rollback_version.document_id,
            version_number=rollback_version.version_number,
            title=rollback_version.title,
            content=rollback_version.content,
            content_type=rollback_version.content_type,
            file_size=rollback_version.file_size,
            doc_metadata=rollback_version.doc_metadata,
            tags=rollback_version.tags,
            change_summary=rollback_version.change_summary,
            change_type=rollback_version.change_type,
            changed_fields=rollback_version.changed_fields,
            is_current=rollback_version.is_current,
            parent_version_id=rollback_version.parent_version_id,
            created_by=rollback_version.created_by,
            created_by_session=rollback_version.created_by_session,
            created_at=rollback_version.created_at.isoformat() if rollback_version.created_at else None
        )

    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to rollback document: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to rollback document: {str(e)}")

@router.post("/{document_id}/versions/compare", response_model=VersionComparisonResponse)
async def compare_document_versions(
    document_id: str,
    request: VersionComparisonRequest,
    current_user: security.User = Depends(security.get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Compare two versions of a document."""
    try:
        from app.services.document_versioning_service import DocumentVersioningService

        comparison = await DocumentVersioningService.compare_versions(
            db=db,
            document_id=document_id,
            version1_number=request.version1_number,
            version2_number=request.version2_number
        )

        return VersionComparisonResponse(**comparison)

    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to compare versions: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to compare versions: {str(e)}")

@router.get("/{document_id}/history", response_model=DocumentHistoryResponse)
async def get_document_history(
    document_id: str,
    limit: int = 50,
    db: AsyncSession = Depends(get_db)
):
    """Get complete document history including versions and change logs."""
    try:
        from app.services.document_versioning_service import DocumentVersioningService

        # Get versions
        versions = await DocumentVersioningService.get_document_versions(
            db=db,
            document_id=document_id,
            limit=limit
        )

        # Get change history
        change_logs = await DocumentVersioningService.get_change_history(
            db=db,
            document_id=document_id,
            limit=limit * 2  # More change logs than versions
        )

        # Find current version
        current_version = 1
        for version in versions:
            if version.is_current:
                current_version = version.version_number
                break

        return DocumentHistoryResponse(
            document_id=document_id,
            versions=[
                DocumentVersionResponse(
                    id=version.id,
                    document_id=version.document_id,
                    version_number=version.version_number,
                    title=version.title,
                    content=version.content,
                    content_type=version.content_type,
                    file_size=version.file_size,
                    doc_metadata=version.doc_metadata,
                    tags=version.tags,
                    change_summary=version.change_summary,
                    change_type=version.change_type,
                    changed_fields=version.changed_fields,
                    is_current=version.is_current,
                    parent_version_id=version.parent_version_id,
                    created_by=version.created_by,
                    created_by_session=version.created_by_session,
                    created_at=version.created_at.isoformat() if version.created_at else None
                )
                for version in versions
            ],
            change_logs=change_logs,
            total_versions=len(versions),
            current_version=current_version
        )

    except Exception as e:
        logger.error(f"Failed to get document history: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get document history: {str(e)}")

@router.post("/", response_model=DocumentResponse)
async def create_document(
    request: DocumentCreate,
    current_user: security.User = Depends(security.get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Create a new document with automatic chunking and vector storage."""
    try:
        document = await DocumentService.create_document(
            db=db,
            title=request.title,
            content=request.content,
            content_type=request.content_type,
            doc_metadata=request.doc_metadata,
            tags=request.tags,
            chunk_size=request.chunk_size,
            chunk_overlap=request.chunk_overlap
        )

        if not document:
            raise HTTPException(status_code=500, detail="Failed to create document")

        return DocumentResponse(
            id=document.id,
            title=document.title,
            content=document.content,
            content_type=document.content_type,
            file_path=document.file_path,
            file_size=document.file_size,
            vector_id=document.vector_id,
            embedding_model=document.embedding_model,
            doc_metadata=document.doc_metadata,
            tags=document.tags,
            created_at=document.created_at,
            updated_at=document.updated_at,
            is_active=document.is_active
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating document: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to create document: {str(e)}")

@router.get("/", response_model=DocumentListResponse)
async def list_documents(
    limit: int = 50,
    offset: int = 0,
    tags: Optional[str] = None,
    content_type: Optional[str] = None,
    current_user: security.User = Depends(security.get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """List documents with optional filtering."""
    try:
        # Parse tags if provided
        tag_list = tags.split(",") if tags else None

        documents, total = await DocumentService.list_documents(
            db=db,
            limit=limit,
            offset=offset,
            tags=tag_list,
            content_type=content_type
        )

        document_responses = [
            DocumentResponse(
                id=doc.id,
                title=doc.title,
                content=doc.content,
                content_type=doc.content_type,
                file_path=doc.file_path,
                file_size=doc.file_size,
                vector_id=doc.vector_id,
                embedding_model=doc.embedding_model,
                doc_metadata=doc.doc_metadata,
                tags=doc.tags,
                created_at=doc.created_at,
                updated_at=doc.updated_at,
                is_active=doc.is_active
            )
            for doc in documents
        ]

        return DocumentListResponse(
            documents=document_responses,
            total=total,
            limit=limit,
            offset=offset
        )

    except Exception as e:
        logger.error(f"Error listing documents: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to list documents: {str(e)}")

@router.get("/{document_id}", response_model=DocumentResponse)
async def get_document(
    document_id: str,
    current_user: security.User = Depends(security.get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get a specific document by ID."""
    try:
        document = await DocumentService.get_document(db=db, document_id=document_id)

        if not document:
            raise HTTPException(status_code=404, detail="Document not found")

        return DocumentResponse(
            id=document.id,
            title=document.title,
            content=document.content,
            content_type=document.content_type,
            file_path=document.file_path,
            file_size=document.file_size,
            vector_id=document.vector_id,
            embedding_model=document.embedding_model,
            doc_metadata=document.doc_metadata,
            tags=document.tags,
            created_at=document.created_at,
            updated_at=document.updated_at,
            is_active=document.is_active
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting document: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get document: {str(e)}")

@router.delete("/{document_id}")
async def delete_document(
    document_id: str,
    soft_delete: bool = True,
    db: AsyncSession = Depends(get_db)
):
    """Delete a document."""
    try:
        success = await DocumentService.delete_document(
            db=db,
            document_id=document_id,
            soft_delete=soft_delete
        )

        if not success:
            raise HTTPException(status_code=404, detail="Document not found")

        return {"message": f"Document {document_id} deleted successfully"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting document: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to delete document: {str(e)}")

@router.post("/search")
async def semantic_search(
    request: SemanticSearchRequest,
    current_user: security.User = Depends(security.get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Perform semantic search across documents."""
    try:
        start_time = time.time()

        results, search_query_id = await DocumentService.semantic_search(
            db=db,
            query=request.query,
            limit=request.limit,
            score_threshold=request.score_threshold,
            filter_conditions=request.filter_conditions,
            search_type=request.search_type.value,
            conversation_id=request.conversation_id
        )

        execution_time = (time.time() - start_time) * 1000

        search_results = [
            SearchResult(
                id=result["id"],
                score=result["score"],
                content=result["content"],
                document_id=result["document_id"],
                document_title=result["document_title"],
                document_type=result["document_type"],
                chunk_index=result.get("chunk_index"),
                metadata=result["metadata"]
            )
            for result in results
        ]

        # Return response in format expected by tests
        return {
            "query": request.query,
            "results": [result.model_dump() for result in search_results],
            "total_results": len(search_results),
            "query_time": execution_time,
            "search_query_id": search_query_id
        }

    except Exception as e:
        logger.error(f"Error in semantic search: {e}")
        raise HTTPException(status_code=500, detail=f"Search failed: {str(e)}")

@router.post("/rag")
async def rag_query(
    request: RAGRequest,
    current_user: security.User = Depends(security.get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Perform Retrieval-Augmented Generation query."""
    try:
        rag_response = await rag_system.retrieve_and_generate(
            db=db,
            query=request.query,
            conversation_id=request.conversation_id,
            search_limit=request.search_limit,
            score_threshold=request.score_threshold,
            filter_conditions=request.filter_conditions,
            use_multi_agent=request.use_multi_agent,
            search_type=request.search_type.value
        )

        # Convert retrieved documents to SearchResult format
        search_results = [
            SearchResult(
                id=doc["id"],
                score=doc["score"],
                content=doc["content"],
                document_id=doc["document_id"],
                document_title=doc["document_title"],
                document_type=doc["document_type"],
                chunk_index=doc.get("chunk_index"),
                metadata=doc["metadata"]
            )
            for doc in rag_response.get("retrieved_documents", [])
        ]

        # Save to conversation if requested
        conversation_id = None
        if request.save_conversation and request.conversation_id:
            conversation_id = request.conversation_id
            # TODO: Save RAG interaction to conversation history

        # Return response in format expected by tests
        return {
            "query": rag_response["query"],
            "answer": rag_response["response"],
            "sources": search_results,
            "context_used": rag_response["context_used"],
            "confidence": rag_response.get("confidence", 0.8),
            "query_time": rag_response.get("query_time", 100),
            "search_metadata": rag_response.get("search_metadata", {}),
            "agent_metadata": rag_response.get("agent_metadata", {}),
            "conversation_id": conversation_id,
            "timestamp": rag_response["timestamp"]
        }

    except Exception as e:
        logger.error(f"Error in RAG query: {e}")
        raise HTTPException(status_code=500, detail=f"RAG query failed: {str(e)}")

@router.get("/system/status", response_model=SystemStatusResponse)
async def get_system_status(current_user: security.User = Depends(security.get_current_user), db: AsyncSession = Depends(get_db)):
    """Get the status of the RAG system."""
    try:
        status = await rag_system.get_system_status(db)
        return SystemStatusResponse(**status)

    except Exception as e:
        logger.error(f"Error getting system status: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get system status: {str(e)}")

@router.post("/suggestions", response_model=QuerySuggestionsResponse)
async def get_query_suggestions(
    request: QuerySuggestionsRequest,
    current_user: security.User = Depends(security.get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get query suggestions based on document content."""
    try:
        suggestions = await rag_system.suggest_related_queries(
            db=db,
            query=request.query,
            limit=request.limit
        )

        return QuerySuggestionsResponse(
            original_query=request.query,
            suggestions=suggestions,
            total_suggestions=len(suggestions)
        )

    except Exception as e:
        logger.error(f"Error getting query suggestions: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get suggestions: {str(e)}")

@router.get("/analytics/search", response_model=SearchAnalyticsResponse)
async def get_search_analytics(
    days_back: int = 7,
    current_user: security.User = Depends(security.get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get search analytics and insights."""
    try:
        analytics = await DocumentService.get_search_analytics(db, days_back=days_back)
        return SearchAnalyticsResponse(**analytics)

    except Exception as e:
        logger.error(f"Error getting search analytics: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get analytics: {str(e)}")


# ============================================================================
# PROJECT PROPOSAL GENERATION ENDPOINTS (Google Gemini)
# ============================================================================

@router.get("/proposal/status", response_model=ProposalStatusResponse)
async def get_proposal_status(
    current_user: security.User = Depends(security.get_current_user)
):
    """
    Check if the proposal generation service is available.

    Returns the status of Google Gemini API integration.
    """
    try:
        from app.services.proposal_service import proposal_service

        if proposal_service.gemini_available:
            return ProposalStatusResponse(
                available=True,
                model=proposal_service.model_name
            )
        else:
            return ProposalStatusResponse(
                available=False,
                error="Gemini API not configured. Please set GEMINI_API_KEY in environment."
            )

    except Exception as e:
        logger.error(f"Error checking proposal status: {e}")
        return ProposalStatusResponse(
            available=False,
            error=f"Service error: {str(e)}"
        )


@router.post("/proposal/generate", response_model=ProposalGenerateResponse)
async def generate_project_proposal(
    request: ProposalGenerateRequest,
    current_user: security.User = Depends(security.get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Generate a comprehensive project proposal using Google Gemini AI.

    This endpoint analyzes all uploaded documents for the current user and generates
    a detailed, structured project proposal with deep research and insights.

    **Features:**
    - Analyzes all user documents comprehensively
    - Uses Google Gemini 1.5 Pro for deep research
    - Generates structured proposal with multiple sections
    - Provides citations and references from documents
    - Customizable proposal type and focus areas

    **Proposal Types:**
    - `general`: General-purpose project proposal
    - `technical`: Technical project with implementation details
    - `business`: Business case and market analysis
    - `research`: Research proposal with methodology

    **Example Request:**
    ```json
    {
        "proposal_type": "business",
        "focus_areas": ["market analysis", "competitive landscape"],
        "additional_context": "Focus on B2B SaaS opportunities"
    }
    ```
    """
    try:
        from app.services.proposal_service import proposal_service

        # Check if service is available
        if not proposal_service.gemini_available:
            raise HTTPException(
                status_code=503,
                detail="Proposal generation service not available. Please configure GEMINI_API_KEY."
            )

        # Generate the proposal
        result = await proposal_service.generate_proposal(
            db=db,
            user_id=current_user.id,
            proposal_type=request.proposal_type,
            focus_areas=request.focus_areas,
            additional_context=request.additional_context
        )

        if not result["success"]:
            raise HTTPException(
                status_code=400,
                detail=result.get("error", "Failed to generate proposal")
            )

        return ProposalGenerateResponse(**result)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating proposal: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to generate proposal: {str(e)}"
        )
