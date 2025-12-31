# app/services/document_service.py
import logging
import time
from typing import List, Dict, Any, Optional, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc, and_
from sqlalchemy.orm import selectinload
import json
from datetime import datetime

from app.database.models import Document, DocumentChunk, SearchQuery
from app.core.vector_store import vector_store

logger = logging.getLogger(__name__)

class DocumentService:
    """
    Service for managing documents, chunks, and semantic search functionality.
    """

    @staticmethod
    async def create_document_record(
        db: AsyncSession,
        *,
        title: str,
        content: str,
        user_id: str,
        content_type: str = "text/plain",
        file_path: Optional[str] = None,
        file_size: Optional[int] = None,
        doc_metadata: Optional[Dict[str, Any]] = None,
        tags: Optional[List[str]] = None,
    ) -> Optional[Document]:
        """Create a document DB record without chunking/vector indexing.
        Use this for fast HTTP responses; then call process_document_content in background.
        """
        try:
            document = Document(
                user_id=user_id,
                title=title,
                content=content,
                content_type=content_type,
                file_path=file_path,
                file_size=file_size or len(content),
                doc_metadata=doc_metadata,
                tags=tags,
                embedding_model=vector_store.embedding_model_name,
            )
            db.add(document)
            await db.commit()
            await db.refresh(document)
            logger.info(f"Created document record {document.id} (no chunks yet)")
            return document
        except Exception as e:
            logger.error(f"Error creating document record: {e}")
            await db.rollback()
            return None

    @staticmethod
    async def process_document_content(
        db: AsyncSession,
        *,
        document_id: str,
        content: str,
        title: str,
        content_type: str,
        doc_metadata: Optional[Dict[str, Any]] = None,
        chunk_size: int = 1000,
        chunk_overlap: int = 200,
    ) -> Tuple[int, List[str]]:
        """Chunk content, index in vector store, and create DocumentChunk rows.
        Returns (chunks_created, vector_ids).
        """
        try:
            # Load the document
            result = await db.execute(select(Document).where(Document.id == document_id))
            document = result.scalar_one_or_none()
            if not document:
                raise ValueError(f"Document {document_id} not found")

            vector_ids: List[str] = []

            # Add full document to vector store
            vector_id = vector_store.add_document(
                content=content,
                metadata={
                    "document_id": document.id,
                    "title": title,
                    "content_type": content_type,
                    "chunk_type": "full_document",
                    **(doc_metadata or {}),
                },
            )
            if vector_id:
                document.vector_id = vector_id
                vector_ids.append(vector_id)

            # Create chunks
            chunks = vector_store.chunk_text(content, chunk_size, chunk_overlap)
            for i, chunk_content in enumerate(chunks):
                start_pos = content.find(chunk_content)
                end_pos = start_pos + len(chunk_content) if start_pos != -1 else None

                chunk = DocumentChunk(
                    document_id=document.id,
                    content=chunk_content,
                    chunk_index=i,
                    chunk_size=len(chunk_content),
                    start_position=start_pos,
                    end_position=end_pos,
                    embedding_model=vector_store.embedding_model_name,
                    chunk_metadata={
                        "document_title": title,
                        "chunk_index": i,
                        "total_chunks": len(chunks),
                    },
                )
                db.add(chunk)
                # Ensure chunk.id is generated before using it in vector metadata
                await db.flush()

                chunk_vector_id = vector_store.add_document(
                    content=chunk_content,
                    metadata={
                        "document_id": document.id,
                        "chunk_id": chunk.id,
                        "title": title,
                        "chunk_index": i,
                        "chunk_type": "chunk",
                        **(doc_metadata or {}),
                    },
                )
                if chunk_vector_id:
                    chunk.vector_id = chunk_vector_id
                    vector_ids.append(chunk_vector_id)

            await db.commit()
            logger.info(f"Processed document {document.id}: {len(chunks)} chunks, {len(vector_ids)} vectors")
            return len(chunks) or 1, vector_ids
        except Exception as e:
            logger.error(f"Error processing document content: {e}")
            await db.rollback()
            return 0, []

    @staticmethod
    async def create_document(
        db: AsyncSession,
        title: str,
        content: str,
        user_id: str,
        content_type: str = "text/plain",
        file_path: Optional[str] = None,
        file_size: Optional[int] = None,
        doc_metadata: Optional[Dict[str, Any]] = None,
        tags: Optional[List[str]] = None,
        chunk_size: int = 1000,
        chunk_overlap: int = 200
    ) -> Optional[Document]:
        """Create a new document with automatic chunking and vector storage."""
        try:
            # Create document record
            document = Document(
                user_id=user_id,
                title=title,
                content=content,
                content_type=content_type,
                file_path=file_path,
                file_size=file_size or len(content),
                doc_metadata=doc_metadata,
                tags=tags,
                embedding_model=vector_store.embedding_model_name
            )

            db.add(document)
            await db.flush()  # Get the document ID

            # Add full document to vector store
            vector_id = vector_store.add_document(
                content=content,
                metadata={
                    "document_id": document.id,
                    "title": title,
                    "content_type": content_type,
                    "chunk_type": "full_document",
                    **(doc_metadata or {})
                }
            )

            if vector_id:
                document.vector_id = vector_id

            # Create chunks
            chunks = vector_store.chunk_text(content, chunk_size, chunk_overlap)

            for i, chunk_content in enumerate(chunks):
                # Calculate positions
                start_pos = content.find(chunk_content)
                end_pos = start_pos + len(chunk_content) if start_pos != -1 else None

                # Create chunk record
                chunk = DocumentChunk(
                    document_id=document.id,
                    content=chunk_content,
                    chunk_index=i,
                    chunk_size=len(chunk_content),
                    start_position=start_pos,
                    end_position=end_pos,
                    embedding_model=vector_store.embedding_model_name,
                    chunk_metadata={
                        "document_title": title,
                        "chunk_index": i,
                        "total_chunks": len(chunks)
                    }
                )
                db.add(chunk)
                await db.flush()

                # Add chunk to vector store
                chunk_vector_id = vector_store.add_document(
                    content=chunk_content,
                    metadata={
                        "document_id": document.id,
                        "chunk_id": chunk.id,
                        "title": title,
                        "chunk_index": i,
                        "chunk_type": "chunk",
                        **(doc_metadata or {})
                    }
                )

                if chunk_vector_id:
                    chunk.vector_id = chunk_vector_id

            await db.commit()
            logger.info(f"Created document {document.id} with {len(chunks)} chunks")
            return document

        except Exception as e:
            logger.error(f"Error creating document: {e}")
            await db.rollback()
            return None
    
    @staticmethod
    async def get_document(
        db: AsyncSession,
        document_id: str,
        include_chunks: bool = False
    ) -> Optional[Document]:
        """Retrieve a document by ID."""
        try:
            query = select(Document).where(
                and_(Document.id == document_id, Document.is_active == True)
            )
            
            if include_chunks:
                query = query.options(selectinload(Document.chunks))
            
            result = await db.execute(query)
            return result.scalar_one_or_none()
            
        except Exception as e:
            logger.error(f"Error retrieving document: {e}")
            return None
    
    @staticmethod
    async def list_documents(
        db: AsyncSession,
        limit: int = 50,
        offset: int = 0,
        tags: Optional[List[str]] = None,
        content_type: Optional[str] = None
    ) -> Tuple[List[Document], int]:
        """List documents with optional filtering."""
        try:
            # Build base query
            query = select(Document).where(Document.is_active == True)
            
            # Apply filters
            if tags:
                # Simple tag filtering - in production, you might want more sophisticated filtering
                for tag in tags:
                    query = query.where(Document.tags.contains(tag))
            
            if content_type:
                query = query.where(Document.content_type == content_type)
            
            # Get total count
            count_query = select(Document.id).where(Document.is_active == True)
            if tags:
                for tag in tags:
                    count_query = count_query.where(Document.tags.contains(tag))
            if content_type:
                count_query = count_query.where(Document.content_type == content_type)
            
            count_result = await db.execute(count_query)
            total = len(count_result.all())
            
            # Apply pagination and ordering
            query = query.order_by(desc(Document.created_at)).limit(limit).offset(offset)
            
            result = await db.execute(query)
            documents = result.scalars().all()
            
            return list(documents), total
            
        except Exception as e:
            logger.error(f"Error listing documents: {e}")
            return [], 0
    
    @staticmethod
    async def semantic_search(
        db: AsyncSession,
        query: str,
        limit: int = 5,
        score_threshold: float = 0.7,
        filter_conditions: Optional[Dict[str, Any]] = None,
        search_type: str = "chunks",  # "chunks", "documents", "both"
        conversation_id: Optional[str] = None
    ) -> Tuple[List[Dict[str, Any]], str]:
        """Perform semantic search across documents."""
        start_time = time.time()
        search_query_id = None
        
        try:
            # Prepare filter conditions for vector store
            vector_filter = {}
            if filter_conditions:
                vector_filter.update(filter_conditions)
            
            # Add search type filter
            if search_type == "chunks":
                vector_filter["chunk_type"] = "chunk"
            elif search_type == "documents":
                vector_filter["chunk_type"] = "full_document"
            
            # Perform vector search
            vector_results = vector_store.search_similar(
                query=query,
                limit=limit * 2,  # Get more results to filter
                score_threshold=score_threshold,
                filter_conditions=vector_filter
            )
            
            # Enrich results with database information
            enriched_results = []
            document_ids = set()
            
            for result in vector_results:
                document_id = result["metadata"].get("document_id")
                if not document_id:
                    continue
                
                # Avoid duplicate documents if searching both types
                if search_type == "both" and document_id in document_ids:
                    continue
                document_ids.add(document_id)
                
                # Get document from database
                document = await DocumentService.get_document(db, document_id)
                if not document:
                    continue
                
                enriched_result = {
                    "id": result["id"],
                    "score": result["score"],
                    "content": result["content"],
                    "document_id": document_id,
                    "document_title": document.title,
                    "document_type": document.content_type,
                    "chunk_index": result["metadata"].get("chunk_index"),
                    "metadata": result["metadata"]
                }
                
                enriched_results.append(enriched_result)
                
                if len(enriched_results) >= limit:
                    break
            
            execution_time = (time.time() - start_time) * 1000
            
            # Log search query
            search_query = SearchQuery(
                query_text=query,
                query_type="semantic",
                limit_requested=limit,
                score_threshold=score_threshold,
                filter_conditions=filter_conditions,
                results_count=len(enriched_results),
                results_metadata={
                    "search_type": search_type,
                    "vector_results_count": len(vector_results)
                },
                execution_time_ms=execution_time,
                conversation_id=conversation_id
            )
            
            db.add(search_query)
            await db.commit()
            search_query_id = search_query.id
            
            logger.info(f"Semantic search completed: {len(enriched_results)} results in {execution_time:.2f}ms")
            return enriched_results, search_query_id
            
        except Exception as e:
            logger.error(f"Error in semantic search: {e}")
            await db.rollback()
            return [], search_query_id
    
    @staticmethod
    async def delete_document(
        db: AsyncSession,
        document_id: str,
        soft_delete: bool = True
    ) -> bool:
        """Delete a document and its chunks."""
        try:
            document = await DocumentService.get_document(db, document_id, include_chunks=True)
            if not document:
                return False
            
            if soft_delete:
                # Soft delete
                document.is_active = False
                await db.commit()
            else:
                # Hard delete - remove from vector store first
                if document.vector_id:
                    vector_store.delete_document(document.vector_id)
                
                for chunk in document.chunks:
                    if chunk.vector_id:
                        vector_store.delete_document(chunk.vector_id)
                
                # Delete from database
                await db.delete(document)
                await db.commit()
            
            logger.info(f"Deleted document {document_id} (soft={soft_delete})")
            return True
            
        except Exception as e:
            logger.error(f"Error deleting document: {e}")
            await db.rollback()
            return False
    
    @staticmethod
    async def get_search_analytics(
        db: AsyncSession,
        days_back: int = 7,
        limit: int = 100
    ) -> Dict[str, Any]:
        """Get search analytics and insights."""
        try:
            # Get recent searches
            query = select(SearchQuery).order_by(desc(SearchQuery.created_at)).limit(limit)
            result = await db.execute(query)
            searches = result.scalars().all()
            
            # Calculate analytics
            total_searches = len(searches)
            avg_execution_time = sum(s.execution_time_ms or 0 for s in searches) / max(total_searches, 1)
            avg_results = sum(s.results_count for s in searches) / max(total_searches, 1)
            
            # Popular queries
            query_counts = {}
            for search in searches:
                query_text = search.query_text.lower().strip()
                query_counts[query_text] = query_counts.get(query_text, 0) + 1
            
            popular_queries = sorted(query_counts.items(), key=lambda x: x[1], reverse=True)[:10]
            
            return {
                "total_searches": total_searches,
                "avg_execution_time_ms": avg_execution_time,
                "avg_results_per_search": avg_results,
                "popular_queries": popular_queries,
                "vector_store_info": vector_store.get_collection_info()
            }
            
        except Exception as e:
            logger.error(f"Error getting search analytics: {e}")
            return {}
