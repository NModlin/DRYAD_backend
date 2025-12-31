"""
Document-related asynchronous tasks for Phase 5.
Handles long-running document processing, indexing, and RAG operations.
"""

import asyncio
import logging
import time
from typing import Dict, Any, List, Optional
from app.core.celery_app import task
from app.database.database import AsyncSessionLocal
from app.services.document_service import DocumentService
from app.core.rag_system import rag_system

logger = logging.getLogger(__name__)

@task(bind=True, name="document_tasks.process_document_batch")
def process_document_batch_task(self, document_data_list: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Asynchronously process a batch of documents.
    
    Args:
        document_data_list: List of document data dictionaries
    
    Returns:
        Dict containing batch processing results
    """
    try:
        self.update_state(
            state='PROGRESS',
            meta={'status': f'Processing {len(document_data_list)} documents'}
        )
        
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        try:
            result = loop.run_until_complete(
                _process_document_batch(document_data_list)
            )
            
            self.update_state(state='SUCCESS', meta={'status': 'Batch processing completed'})
            return result
            
        finally:
            loop.close()
            
    except Exception as e:
        logger.error(f"Document batch processing failed: {str(e)}")
        self.update_state(
            state='FAILURE',
            meta={'status': 'Batch processing failed', 'error': str(e)}
        )
        raise

async def _process_document_batch(document_data_list: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Process a batch of documents asynchronously."""
    
    async with AsyncSessionLocal() as db:
        results = []
        successful = 0
        failed = 0
        
        for doc_data in document_data_list:
            try:
                # Create document
                document = await DocumentService.create_document(
                    db=db,
                    title=doc_data.get("title", "Untitled"),
                    content=doc_data.get("content", ""),
                    content_type=doc_data.get("content_type", "text/plain"),
                    doc_metadata=doc_data.get("metadata", {}),
                    tags=doc_data.get("tags", []),
                    chunk_size=doc_data.get("chunk_size", 1000),
                    chunk_overlap=doc_data.get("chunk_overlap", 200)
                )
                
                results.append({
                    "title": doc_data.get("title"),
                    "document_id": document.id,
                    "status": "success",
                    "chunks_created": len(document.chunks)
                })
                successful += 1
                
            except Exception as e:
                results.append({
                    "title": doc_data.get("title"),
                    "document_id": None,
                    "status": "failed",
                    "error": str(e)
                })
                failed += 1
        
        return {
            "total_documents": len(document_data_list),
            "successful": successful,
            "failed": failed,
            "results": results,
            "status": "completed"
        }

@task(bind=True, name="document_tasks.rebuild_vector_index")
def rebuild_vector_index_task(self, collection_name: Optional[str] = None) -> Dict[str, Any]:
    """
    Asynchronously rebuild the vector index for documents.
    
    Args:
        collection_name: Optional specific collection to rebuild
    
    Returns:
        Dict containing rebuild results
    """
    try:
        self.update_state(state='PROGRESS', meta={'status': 'Rebuilding vector index'})
        
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        try:
            result = loop.run_until_complete(
                _rebuild_vector_index(collection_name)
            )
            
            self.update_state(state='SUCCESS', meta={'status': 'Vector index rebuilt'})
            return result
            
        finally:
            loop.close()
            
    except Exception as e:
        logger.error(f"Vector index rebuild failed: {str(e)}")
        self.update_state(
            state='FAILURE',
            meta={'status': 'Index rebuild failed', 'error': str(e)}
        )
        raise

async def _rebuild_vector_index(collection_name: Optional[str]) -> Dict[str, Any]:
    """Rebuild vector index asynchronously."""
    
    async with AsyncSessionLocal() as db:
        try:
            from app.core.vector_store import vector_store
            
            # Get all documents
            documents = await DocumentService.list_documents(db, limit=1000)
            
            indexed_count = 0
            failed_count = 0
            
            for document in documents.items:
                try:
                    # Re-index document chunks
                    for chunk in document.chunks:
                        if chunk.vector_id:
                            # Remove old vector
                            vector_store.delete_document(chunk.vector_id)
                        
                        # Add new vector
                        vector_id = vector_store.add_document(
                            content=chunk.content,
                            metadata={
                                "document_id": str(document.id),
                                "chunk_id": str(chunk.id),
                                "title": document.title,
                                "tags": document.tags
                            }
                        )
                        
                        # Update chunk with new vector ID
                        chunk.vector_id = vector_id
                        await db.commit()
                    
                    indexed_count += 1
                    
                except Exception as e:
                    logger.error(f"Failed to index document {document.id}: {str(e)}")
                    failed_count += 1
            
            return {
                "total_documents": len(documents.items),
                "indexed_successfully": indexed_count,
                "failed": failed_count,
                "collection_name": collection_name or "default",
                "status": "completed"
            }
            
        except Exception as e:
            logger.error(f"Vector index rebuild failed: {str(e)}")
            raise

@task(bind=True, name="document_tasks.run_complex_rag_query")
def run_complex_rag_query_task(self, query: str, search_limit: int = 5,
                              use_multi_agent: bool = False,
                              conversation_id: Optional[str] = None,
                              save_conversation: bool = True) -> Dict[str, Any]:
    """
    Asynchronously execute a complex RAG query with optional multi-agent processing.
    
    Args:
        query: The query to process
        search_limit: Number of documents to retrieve
        use_multi_agent: Whether to use multi-agent processing
        conversation_id: Optional conversation ID
        save_conversation: Whether to save the conversation
    
    Returns:
        Dict containing RAG query results
    """
    try:
        self.update_state(state='PROGRESS', meta={'status': 'Processing RAG query'})
        
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        try:
            result = loop.run_until_complete(
                _execute_complex_rag_query(
                    query, search_limit, use_multi_agent, conversation_id, save_conversation
                )
            )
            
            self.update_state(state='SUCCESS', meta={'status': 'RAG query completed'})
            return result
            
        finally:
            loop.close()
            
    except Exception as e:
        logger.error(f"Complex RAG query failed: {str(e)}")
        self.update_state(
            state='FAILURE',
            meta={'status': 'RAG query failed', 'error': str(e)}
        )
        raise

async def _execute_complex_rag_query(query: str, search_limit: int,
                                   use_multi_agent: bool, conversation_id: Optional[str],
                                   save_conversation: bool) -> Dict[str, Any]:
    """Execute complex RAG query asynchronously."""
    
    async with AsyncSessionLocal() as db:
        try:
            start_time = time.time()
            
            # Get conversation context if provided
            context = []
            if conversation_id:
                from app.services.chat_history import ChatHistoryService
                conversation = await ChatHistoryService.get_conversation(db, conversation_id)
                if conversation:
                    context = [
                        {"role": msg.role, "content": msg.content}
                        for msg in conversation.messages[-5:]  # Last 5 messages
                    ]
            
            # Execute RAG query
            rag_result = await rag_system.retrieve_and_generate(
                db=db,
                query=query,
                search_limit=search_limit,
                score_threshold=0.1,
                use_multi_agent=use_multi_agent,
                conversation_context=context
            )
            
            execution_time = time.time() - start_time
            
            # Save conversation if requested
            if save_conversation:
                from app.services.chat_history import ChatHistoryService
                
                if not conversation_id:
                    conversation = await ChatHistoryService.create_conversation(
                        db=db,
                        title=f"RAG Query: {query[:50]}...",
                        initial_message=query
                    )
                    conversation_id = conversation.id
                
                # Add RAG response
                await ChatHistoryService.add_message(
                    db=db,
                    conversation_id=conversation_id,
                    role="assistant",
                    content=rag_result.get("response", ""),
                    metadata={
                        "rag_used": True,
                        "multi_agent_used": use_multi_agent,
                        "retrieved_documents": len(rag_result.get("retrieved_documents", [])),
                        "execution_time": execution_time,
                        "task_type": "complex_rag_query"
                    }
                )
            
            return {
                "query": query,
                "response": rag_result.get("response", ""),
                "retrieved_documents": rag_result.get("retrieved_documents", []),
                "context_used": rag_result.get("context_used", False),
                "multi_agent_used": use_multi_agent,
                "conversation_id": conversation_id,
                "execution_time": execution_time,
                "status": "completed"
            }
            
        except Exception as e:
            logger.error(f"Complex RAG query execution failed: {str(e)}")
            raise

@task(bind=True, name="document_tasks.analyze_document_collection")
def analyze_document_collection_task(self, analysis_type: str = "summary") -> Dict[str, Any]:
    """
    Asynchronously analyze the entire document collection.
    
    Args:
        analysis_type: Type of analysis to perform (summary, trends, etc.)
    
    Returns:
        Dict containing analysis results
    """
    try:
        self.update_state(state='PROGRESS', meta={'status': 'Analyzing document collection'})
        
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        try:
            result = loop.run_until_complete(
                _analyze_document_collection(analysis_type)
            )
            
            self.update_state(state='SUCCESS', meta={'status': 'Analysis completed'})
            return result
            
        finally:
            loop.close()
            
    except Exception as e:
        logger.error(f"Document collection analysis failed: {str(e)}")
        self.update_state(
            state='FAILURE',
            meta={'status': 'Analysis failed', 'error': str(e)}
        )
        raise

async def _analyze_document_collection(analysis_type: str) -> Dict[str, Any]:
    """Analyze document collection asynchronously."""
    
    async with AsyncSessionLocal() as db:
        try:
            # Get all documents
            documents = await DocumentService.list_documents(db, limit=1000)
            
            if analysis_type == "summary":
                # Create collection summary
                total_docs = len(documents.items)
                total_chunks = sum(len(doc.chunks) for doc in documents.items)
                
                # Analyze tags
                all_tags = []
                for doc in documents.items:
                    all_tags.extend(doc.tags)
                
                tag_counts = {}
                for tag in all_tags:
                    tag_counts[tag] = tag_counts.get(tag, 0) + 1
                
                # Most common tags
                common_tags = sorted(tag_counts.items(), key=lambda x: x[1], reverse=True)[:10]
                
                return {
                    "analysis_type": analysis_type,
                    "total_documents": total_docs,
                    "total_chunks": total_chunks,
                    "average_chunks_per_document": total_chunks / total_docs if total_docs > 0 else 0,
                    "common_tags": common_tags,
                    "unique_tags": len(tag_counts),
                    "status": "completed"
                }
            
            else:
                return {
                    "analysis_type": analysis_type,
                    "status": "unsupported_analysis_type",
                    "error": f"Analysis type '{analysis_type}' is not supported"
                }
                
        except Exception as e:
            logger.error(f"Document collection analysis failed: {str(e)}")
            raise
