# app/services/advanced_search_service.py
import logging
import time
from typing import List, Dict, Any, Optional, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, or_, desc, asc, text
from datetime import datetime

from app.database.models import Document
from app.core.vector_store import vector_store
from app.api.v1.schemas.documents import AdvancedSearchRequest, AdvancedSearchResponse, SearchResult, SearchFacet

logger = logging.getLogger(__name__)

class AdvancedSearchService:
    """Service for advanced document search with faceted filtering and sorting."""
    
    @staticmethod
    async def advanced_search(
        db: AsyncSession,
        request: AdvancedSearchRequest
    ) -> AdvancedSearchResponse:
        """Perform advanced search with faceted filtering and sorting."""
        start_time = time.time()
        
        try:
            # Step 1: Build database query with filters
            query = select(Document).where(Document.is_active == True)
            
            # Apply filters
            filters_applied = {}
            
            # Content type filter
            if request.content_types:
                query = query.where(Document.content_type.in_(request.content_types))
                filters_applied["content_types"] = request.content_types
            
            # Date range filter
            if request.date_from:
                query = query.where(Document.created_at >= request.date_from)
                filters_applied["date_from"] = request.date_from.isoformat()
            
            if request.date_to:
                query = query.where(Document.created_at <= request.date_to)
                filters_applied["date_to"] = request.date_to.isoformat()
            
            # File size filter
            if request.file_size_min is not None:
                query = query.where(Document.file_size >= request.file_size_min)
                filters_applied["file_size_min"] = request.file_size_min
            
            if request.file_size_max is not None:
                query = query.where(Document.file_size <= request.file_size_max)
                filters_applied["file_size_max"] = request.file_size_max
            
            # Tags filter (JSON array contains)
            if request.tags:
                for tag in request.tags:
                    query = query.where(func.json_contains(Document.tags, f'"{tag}"'))
                filters_applied["tags"] = request.tags
            
            # Metadata filters
            if request.metadata_filters:
                for key, value in request.metadata_filters.items():
                    if isinstance(value, str):
                        query = query.where(func.json_extract(Document.doc_metadata, f'$.{key}') == value)
                    elif isinstance(value, list):
                        query = query.where(func.json_extract(Document.doc_metadata, f'$.{key}').in_(value))
                filters_applied["metadata_filters"] = request.metadata_filters
            
            # Step 2: Get total count before pagination
            count_query = select(func.count()).select_from(query.subquery())
            total_result = await db.execute(count_query)
            total_results = total_result.scalar() or 0
            
            # Step 3: Apply sorting
            if request.sort_by == "date":
                sort_column = Document.created_at
            elif request.sort_by == "title":
                sort_column = Document.title
            elif request.sort_by == "file_size":
                sort_column = Document.file_size
            else:  # relevance - will be handled by vector search
                sort_column = Document.created_at
            
            if request.sort_order == "asc":
                query = query.order_by(asc(sort_column))
            else:
                query = query.order_by(desc(sort_column))
            
            # Step 4: Apply pagination
            query = query.offset(request.offset).limit(request.limit)
            
            # Step 5: Execute database query
            db_result = await db.execute(query)
            documents = db_result.scalars().all()
            
            # Step 6: Perform vector search if needed
            search_results = []
            
            if request.search_type in ["semantic", "hybrid"] and vector_store.is_connected:
                # Get document IDs for vector search filtering
                doc_ids = [doc.id for doc in documents] if documents else None
                
                try:
                    vector_results = await vector_store.search_similar(
                        query=request.query,
                        limit=min(request.limit * 2, 100),  # Get more results for better ranking
                        score_threshold=request.score_threshold,
                        filter_conditions={"document_id": doc_ids} if doc_ids else None
                    )
                    
                    # Convert vector results to SearchResult format
                    for result in vector_results:
                        # Find corresponding document
                        doc = next((d for d in documents if d.id == result.get("document_id")), None)
                        if doc:
                            search_results.append(SearchResult(
                                id=result["id"],
                                score=result["score"],
                                content=result["content"][:500] + "..." if len(result["content"]) > 500 else result["content"],
                                document_id=doc.id,
                                document_title=doc.title,
                                document_type=doc.content_type,
                                chunk_index=result.get("chunk_index", 0),
                                metadata={
                                    "file_size": doc.file_size,
                                    "created_at": doc.created_at.isoformat() if doc.created_at else None,
                                    "tags": doc.tags,
                                    "doc_metadata": doc.doc_metadata
                                }
                            ))
                
                except Exception as e:
                    logger.error(f"Vector search failed: {e}")
                    # Fallback to database results
                    pass
            
            # Step 7: Fallback to database results if no vector results
            if not search_results:
                for doc in documents:
                    # Simple text matching score
                    content_lower = doc.content.lower()
                    query_lower = request.query.lower()
                    score = 1.0 if query_lower in content_lower else 0.5
                    
                    search_results.append(SearchResult(
                        id=doc.id,
                        score=score,
                        content=doc.content[:500] + "..." if len(doc.content) > 500 else doc.content,
                        document_id=doc.id,
                        document_title=doc.title,
                        document_type=doc.content_type,
                        chunk_index=0,
                        metadata={
                            "file_size": doc.file_size,
                            "created_at": doc.created_at.isoformat() if doc.created_at else None,
                            "tags": doc.tags,
                            "doc_metadata": doc.doc_metadata
                        }
                    ))
            
            # Step 8: Apply relevance sorting if requested
            if request.sort_by == "relevance":
                search_results.sort(key=lambda x: x.score, reverse=(request.sort_order == "desc"))
            
            # Step 9: Generate facets if requested
            facets = []
            if request.include_facets:
                facets = await AdvancedSearchService._generate_facets(db, request)
            
            # Step 10: Calculate execution time
            search_time_ms = (time.time() - start_time) * 1000
            
            return AdvancedSearchResponse(
                query=request.query,
                results=search_results[:request.limit],  # Ensure we don't exceed limit
                total_results=total_results,
                limit=request.limit,
                offset=request.offset,
                search_time_ms=search_time_ms,
                facets=facets,
                search_metadata={
                    "search_type": request.search_type,
                    "vector_search_used": bool(vector_store.is_connected and request.search_type in ["semantic", "hybrid"]),
                    "database_results": len(documents),
                    "vector_results": len(search_results) if vector_store.is_connected else 0
                },
                filters_applied=filters_applied
            )
            
        except Exception as e:
            logger.error(f"Advanced search failed: {e}")
            raise
    
    @staticmethod
    async def _generate_facets(
        db: AsyncSession,
        request: AdvancedSearchRequest
    ) -> List[SearchFacet]:
        """Generate facets for search results."""
        facets = []
        
        try:
            # Base query for facet generation
            base_query = select(Document).where(Document.is_active == True)
            
            # Content type facet
            if not request.facet_fields or "content_type" in request.facet_fields:
                content_type_query = select(
                    Document.content_type,
                    func.count(Document.id).label('count')
                ).where(Document.is_active == True).group_by(Document.content_type)
                
                result = await db.execute(content_type_query)
                content_type_counts = {row.content_type: row.count for row in result}
                
                facets.append(SearchFacet(
                    field="content_type",
                    values=content_type_counts
                ))
            
            # Date range facet (by month)
            if not request.facet_fields or "date_range" in request.facet_fields:
                date_query = select(
                    func.date_format(Document.created_at, '%Y-%m').label('month'),
                    func.count(Document.id).label('count')
                ).where(Document.is_active == True).group_by(
                    func.date_format(Document.created_at, '%Y-%m')
                )
                
                result = await db.execute(date_query)
                date_counts = {row.month: row.count for row in result if row.month}
                
                facets.append(SearchFacet(
                    field="date_range",
                    values=date_counts
                ))
            
            # File size ranges facet
            if not request.facet_fields or "file_size_range" in request.facet_fields:
                size_ranges = {
                    "small (< 1KB)": (0, 1024),
                    "medium (1KB - 100KB)": (1024, 102400),
                    "large (100KB - 10MB)": (102400, 10485760),
                    "very_large (> 10MB)": (10485760, float('inf'))
                }
                
                size_counts = {}
                for range_name, (min_size, max_size) in size_ranges.items():
                    if max_size == float('inf'):
                        size_query = select(func.count(Document.id)).where(
                            and_(Document.is_active == True, Document.file_size >= min_size)
                        )
                    else:
                        size_query = select(func.count(Document.id)).where(
                            and_(
                                Document.is_active == True,
                                Document.file_size >= min_size,
                                Document.file_size < max_size
                            )
                        )
                    
                    result = await db.execute(size_query)
                    count = result.scalar() or 0
                    if count > 0:
                        size_counts[range_name] = count
                
                facets.append(SearchFacet(
                    field="file_size_range",
                    values=size_counts
                ))
            
        except Exception as e:
            logger.error(f"Facet generation failed: {e}")
        
        return facets
