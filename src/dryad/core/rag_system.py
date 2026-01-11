# app/core/rag_system.py
import logging
from typing import List, Dict, Any, Optional, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime

from dryad.core.vector_store import vector_store
# Optional import: multi-agent orchestrator (DRYAD built-in implementation)
try:
    from dryad.core.multi_agent import multi_agent_orchestrator
except Exception:
    multi_agent_orchestrator = None
from dryad.core.llm_config import get_llm, get_llm_info

logger = logging.getLogger(__name__)

class RAGSystem:
    """
    Retrieval-Augmented Generation system that combines semantic search
    with agent responses for enhanced, context-aware answers.
    """
    
    def __init__(
        self,
        default_search_limit: int = 5,
        default_score_threshold: float = 0.7,
        max_context_length: int = 4000
    ):
        """Initialize the RAG system."""
        self.default_search_limit = default_search_limit
        self.default_score_threshold = default_score_threshold
        self.max_context_length = max_context_length
    
    async def retrieve_and_generate(
        self,
        db: AsyncSession,
        query: str,
        conversation_id: Optional[str] = None,
        search_limit: Optional[int] = None,
        score_threshold: Optional[float] = None,
        filter_conditions: Optional[Dict[str, Any]] = None,
        use_multi_agent: bool = False,
        search_type: str = "chunks"
    ) -> Dict[str, Any]:
        """
        Perform retrieval-augmented generation.
        
        Args:
            db: Database session
            query: User query
            conversation_id: Optional conversation ID for context
            search_limit: Number of documents to retrieve
            score_threshold: Minimum similarity score
            filter_conditions: Additional filters for search
            use_multi_agent: Whether to use multi-agent system
            search_type: Type of search ("chunks", "documents", "both")
        
        Returns:
            Dict containing the generated response and metadata
        """
        try:
            # Use defaults if not specified
            search_limit = search_limit or self.default_search_limit
            score_threshold = score_threshold or self.default_score_threshold
            
            # Step 1: Retrieve relevant documents from Weaviate
            logger.info(f"Searching Weaviate for query: {query}")
            retrieved_docs = []
            search_query_id = None

            if vector_store.is_connected:
                # Use Weaviate for semantic search
                search_results = vector_store.search_similar(
                    query=query,
                    limit=search_limit,
                    score_threshold=score_threshold,
                    filter_conditions=filter_conditions
                )

                # Convert Weaviate results to expected format
                retrieved_docs = []
                for result in search_results:
                    retrieved_docs.append({
                        "id": result["id"],
                        "content": result["content"],
                        "score": result["score"],
                        "document_title": result.get("document_title", ""),
                        "document_type": result.get("document_type", "text/plain"),
                        "chunk_index": result.get("chunk_index", 0),
                        "metadata": result["metadata"]
                    })

                logger.info(f"Retrieved {len(retrieved_docs)} documents from Weaviate")
            else:
                logger.warning("Weaviate not connected - no documents retrieved")

            # Step 2: Prepare context from retrieved documents
            context = self._prepare_context(retrieved_docs, query)

            # Step 3: Generate response using LLM with context
            if retrieved_docs and context:
                # We have relevant documents - use RAG
                logger.info("Generating RAG response with retrieved context")
                enhanced_prompt = self._create_rag_prompt(query, context)

                if use_multi_agent and multi_agent_orchestrator.llm is not None:
                    # Use multi-agent system for complex reasoning
                    agent_response = multi_agent_orchestrator.execute_simple_query(
                        query=enhanced_prompt,
                        context=context
                    )
                else:
                    # Use direct LLM response with context
                    response_text = self._generate_context_based_response(query, context)
                    agent_response = {
                        "query": query,
                        "result": response_text,
                        "agents_used": ["rag_system"],
                        "task_type": "rag_response"
                    }
            else:
                # No relevant documents found - provide informative response
                logger.info("No relevant documents found - providing general response")
                no_context_response = self._generate_no_context_response(query)
                agent_response = {
                    "query": query,
                    "result": no_context_response,
                    "agents_used": ["llm_only"],
                    "task_type": "no_context_response"
                }
            
            # Step 5: Prepare final response
            rag_response = {
                "query": query,
                "response": agent_response.get("result", ""),
                "retrieved_documents": retrieved_docs,
                "context_used": len(retrieved_docs) > 0,
                "search_metadata": {
                    "search_query_id": search_query_id,
                    "documents_found": len(retrieved_docs),
                    "search_type": search_type,
                    "score_threshold": score_threshold
                },
                "agent_metadata": {
                    "agents_used": agent_response.get("agents_used", []),
                    "task_type": agent_response.get("task_type", "unknown"),
                    "use_multi_agent": use_multi_agent
                },
                "timestamp": datetime.utcnow().isoformat()
            }
            
            logger.info(f"RAG response generated for query with {len(retrieved_docs)} retrieved documents")
            return rag_response
            
        except Exception as e:
            logger.error(f"Error in RAG system: {e}")
            return {
                "query": query,
                "response": f"I apologize, but I encountered an error while processing your request: {str(e)}",
                "retrieved_documents": [],
                "context_used": False,
                "search_metadata": {
                    "search_query_id": None,
                    "documents_found": 0,
                    "search_type": search_type,
                    "score_threshold": score_threshold
                },
                "agent_metadata": {
                    "agents_used": [],
                    "task_type": "error",
                    "use_multi_agent": use_multi_agent
                },
                "timestamp": datetime.utcnow().isoformat(),
                "error": str(e)
            }
    
    def _prepare_context(self, retrieved_docs: List[Dict[str, Any]], query: str) -> str:
        """Prepare context string from retrieved documents."""
        if not retrieved_docs:
            return ""
        
        context_parts = []
        current_length = 0
        
        # Sort by relevance score
        sorted_docs = sorted(retrieved_docs, key=lambda x: x["score"], reverse=True)
        
        for i, doc in enumerate(sorted_docs):
            # Create context entry
            doc_context = f"Document {i+1} (Score: {doc['score']:.3f}):\n"
            doc_context += f"Title: {doc['document_title']}\n"
            doc_context += f"Content: {doc['content']}\n"
            
            # Check if adding this document would exceed max length
            if current_length + len(doc_context) > self.max_context_length:
                break
            
            context_parts.append(doc_context)
            current_length += len(doc_context)
        
        return "\n---\n".join(context_parts)
    
    def _create_rag_prompt(self, query: str, context: str) -> str:
        """Create an enhanced prompt that includes retrieved context."""
        if not context:
            return query
        
        prompt = f"""Based on the following relevant documents, please answer the user's question. Use the information from the documents to provide a comprehensive and accurate response. If the documents don't contain enough information to fully answer the question, please indicate what additional information might be needed.

RELEVANT DOCUMENTS:
{context}

USER QUESTION: {query}

Please provide a detailed response based on the above documents:"""
        
        return prompt
    
    def _generate_context_based_response(self, query: str, context: str) -> str:
        """Generate a response based on context using the available LLM."""
        if not context:
            return self._generate_no_context_response(query)

        try:
            # Try to use the configured LLM
            llm = get_llm()
            llm_info = get_llm_info()

            if llm and llm_info.get("available", False):
                # Create a focused RAG prompt
                rag_prompt = self._create_rag_prompt(query, context)

                # Generate response using LLM
                response = llm.invoke(rag_prompt)

                # Extract text from response (handle different LLM response formats)
                if hasattr(response, 'content'):
                    return response.content
                elif isinstance(response, str):
                    return response
                else:
                    return str(response)
            else:
                # Fallback to template-based response
                return self._generate_template_response(query, context)

        except Exception as e:
            logger.error(f"Error generating LLM response: {e}")
            return self._generate_template_response(query, context)

    def _generate_no_context_response(self, query: str) -> str:
        """Generate a response when no relevant documents are found."""
        try:
            # Try to use LLM for general response
            llm = get_llm()
            llm_info = get_llm_info()

            if llm and llm_info.get("available", False):
                no_context_prompt = f"""I don't have any specific documents in my knowledge base that directly answer this question: "{query}"

Please provide a helpful general response based on your training knowledge, but clearly indicate that this is general information and not based on specific documents in the knowledge base.

Question: {query}"""

                response = llm.invoke(no_context_prompt)

                # Extract text from response
                if hasattr(response, 'content'):
                    return response.content
                elif isinstance(response, str):
                    return response
                else:
                    return str(response)
            else:
                # Fallback message
                return f"I couldn't find any relevant documents to answer your question about '{query}'. You might want to try rephrasing your query or adding more documents to the knowledge base."

        except Exception as e:
            logger.error(f"Error generating no-context response: {e}")
            return f"I couldn't find any relevant documents to answer your question about '{query}'. You might want to try rephrasing your query or adding more documents to the knowledge base."

    def _generate_template_response(self, query: str, context: str) -> str:
        """Generate a template-based response when LLM is not available."""
        response = f"Based on the available documents, here's what I found regarding your question about '{query}':\n\n"

        # Extract key information from context
        lines = context.split('\n')
        content_lines = [line for line in lines if line.startswith('Content:')]

        if content_lines:
            response += "Key information from the documents:\n"
            for i, line in enumerate(content_lines[:3]):  # Limit to top 3 results
                content = line.replace('Content:', '').strip()
                if content:
                    response += f"• {content[:200]}{'...' if len(content) > 200 else ''}\n"

        response += "\nThis information is based on the documents in the knowledge base. For more detailed information, you may want to review the full documents or ask more specific questions."

        return response
    
    async def add_document_from_text(
        self,
        db: AsyncSession,
        title: str,
        content: str,
        content_type: str = "text/plain",
        doc_metadata: Optional[Dict[str, Any]] = None,
        tags: Optional[List[str]] = None,
        image_data: Optional[bytes] = None
    ) -> Optional[str]:
        """Add a document to the RAG system from text content with optional multimodal data."""
        try:
            # Import here to avoid circular dependency
            from dryad.services.document_service import DocumentService

            # Step 1: Create document in database
            document = await DocumentService.create_document(
                db=db,
                title=title,
                content=content,
                content_type=content_type,
                doc_metadata=doc_metadata,
                tags=tags
            )

            if not document:
                logger.error("Failed to create document in database")
                return None

            # Step 2: Add to Weaviate vector store
            if vector_store.is_connected:
                # Prepare metadata for Weaviate
                weaviate_metadata = {
                    "document_id": str(document.id),
                    "title": title,
                    "content_type": content_type,
                    "chunk_type": "full_document",
                    "chunk_index": 0,
                    **(doc_metadata or {})
                }

                # Add to vector store (with optional image data for multimodal)
                vector_id = vector_store.add_document(
                    content=content,
                    metadata=weaviate_metadata,
                    document_id=str(document.id),
                    image_data=image_data
                )

                if vector_id:
                    logger.info(f"Added document to Weaviate: {document.id} -> {vector_id}")
                else:
                    logger.warning(f"Failed to add document to Weaviate: {document.id}")
            else:
                logger.warning("Weaviate not connected - document only stored in database")

            # Step 3: Process chunks if document is large
            if len(content) > self.max_context_length:
                await self._add_document_chunks(db, document, content, doc_metadata, image_data)

            logger.info(f"Successfully added document to RAG system: {document.id}")
            return str(document.id)

        except Exception as e:
            logger.error(f"Error adding document to RAG system: {e}")
            return None

    async def _add_document_chunks(
        self,
        db: AsyncSession,
        document,
        content: str,
        doc_metadata: Optional[Dict[str, Any]] = None,
        image_data: Optional[bytes] = None
    ):
        """Add document chunks to Weaviate for better retrieval."""
        if not vector_store.is_connected:
            return

        try:
            # Split content into chunks
            chunks = vector_store.chunk_text(content, chunk_size=1000, overlap=200)

            for i, chunk in enumerate(chunks):
                chunk_metadata = {
                    "document_id": str(document.id),
                    "title": document.title,
                    "content_type": document.content_type,
                    "chunk_type": "chunk",
                    "chunk_index": i,
                    "chunk_id": f"{document.id}_chunk_{i}",
                    **(doc_metadata or {})
                }

                # Add chunk to Weaviate
                vector_id = vector_store.add_document(
                    content=chunk,
                    metadata=chunk_metadata,
                    document_id=f"{document.id}_chunk_{i}",
                    image_data=image_data if i == 0 else None  # Only add image to first chunk
                )

                if vector_id:
                    logger.debug(f"Added chunk {i} to Weaviate: {vector_id}")
                else:
                    logger.warning(f"Failed to add chunk {i} to Weaviate")

        except Exception as e:
            logger.error(f"Error adding document chunks: {e}")
    
    async def get_system_status(self, db: AsyncSession) -> Dict[str, Any]:
        """Get the status of the RAG system with Weaviate integration."""
        try:
            # Import here to avoid circular dependency
            from dryad.services.document_service import DocumentService

            # Get document statistics from database
            documents, total_docs = await DocumentService.list_documents(db, limit=1)

            # Get Weaviate vector store info
            vector_info = vector_store.get_collection_info()
            capabilities = vector_store.get_capabilities()

            # Get LLM info
            llm_info = get_llm_info()

            # Determine overall system status
            if vector_store.is_connected and llm_info.get("available", False):
                status = "fully_operational"
            elif vector_store.is_connected:
                status = "vector_only"  # Vector search works but LLM limited
            elif llm_info.get("available", False):
                status = "llm_only"  # LLM works but no vector search
            else:
                status = "limited"  # Both have issues

            return {
                "status": status,
                "total_documents": total_docs,  # Match schema field name
                "vector_store": {
                    **vector_info,
                    "capabilities": capabilities
                },
                "search_analytics": {  # Add required field
                    "total_searches": 0,  # Would be tracked in production
                    "avg_response_time": 0.0,
                    "popular_queries": [],
                    "search_success_rate": 1.0
                },
                "configuration": {
                    "default_search_limit": self.default_search_limit,
                    "default_score_threshold": self.default_score_threshold,
                    "max_context_length": self.max_context_length,
                    "vector_store_type": "Weaviate",
                    "embedding_model": vector_store.embedding_model_name if hasattr(vector_store, 'embedding_model_name') else "unknown",
                    "llm_status": {
                        "provider": llm_info.get("provider", "unknown"),
                        "model": llm_info.get("model_name", "unknown"),
                        "available": llm_info.get("available", False)
                    },
                    "features": {
                        "semantic_search": vector_store.is_connected,
                        "multimodal_search": capabilities.get("multimodal_embeddings", False),
                        "rag_generation": llm_info.get("available", False),
                        "document_chunking": True,
                        "cross_modal_search": capabilities.get("clip_available", False)
                    }
                }
            }

        except Exception as e:
            logger.error(f"Error getting RAG system status: {e}")
            return {
                "status": "error",
                "total_documents": 0,
                "vector_store": {"connected": False},
                "search_analytics": {
                    "total_searches": 0,
                    "avg_response_time": 0.0,
                    "popular_queries": [],
                    "search_success_rate": 0.0
                },
                "configuration": {
                    "default_search_limit": self.default_search_limit,
                    "default_score_threshold": self.default_score_threshold,
                    "max_context_length": self.max_context_length,
                    "vector_store_type": "Weaviate",
                    "embedding_model": "unknown",
                    "error": str(e)
                }
            }
    
    async def suggest_related_queries(
        self,
        db: AsyncSession,
        query: str,
        limit: int = 5
    ) -> List[str]:
        """Suggest related queries based on document content."""
        try:
            # Import here to avoid circular dependency
            from dryad.services.document_service import DocumentService

            # Get similar documents
            retrieved_docs, _ = await DocumentService.semantic_search(
                db=db,
                query=query,
                limit=limit * 2,
                score_threshold=0.5,
                search_type="chunks"
            )
            
            # Extract potential related queries from document titles and content
            suggestions = set()
            
            for doc in retrieved_docs:
                title = doc.get("document_title", "")
                content = doc.get("content", "")
                
                # Simple heuristic: extract questions from content
                sentences = content.split('.')
                for sentence in sentences:
                    sentence = sentence.strip()
                    if any(word in sentence.lower() for word in ['what', 'how', 'why', 'when', 'where']):
                        if len(sentence) < 100:  # Keep suggestions concise
                            suggestions.add(sentence)
                
                # Add variations based on title
                if title and len(title) < 100:
                    suggestions.add(f"Tell me more about {title}")
                    suggestions.add(f"How does {title} work?")
            
            # Return top suggestions
            return list(suggestions)[:limit]
            
        except Exception as e:
            logger.error(f"Error generating query suggestions: {e}")
            return []


# Global RAG system instance
rag_system = RAGSystem()
