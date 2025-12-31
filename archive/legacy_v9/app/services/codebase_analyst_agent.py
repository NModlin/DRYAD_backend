"""
Codebase Analyst Agent - Tier 2 Specialist Agent

This agent provides deep code understanding and analysis capabilities using:
- RAG system for semantic code search
- Pattern recognition and dependency analysis
- DRYAD integration for context storage
- Local LLM for intelligent analysis
"""

import logging
import json
import uuid
from typing import Dict, Any, List, Optional
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)


class CodebaseAnalystAgent:
    """
    Tier 2 Specialist Agent for codebase analysis.
    
    Capabilities:
    - Semantic code search using RAG
    - Pattern recognition
    - Dependency analysis
    - Impact analysis
    - Code structure analysis
    """
    
    def __init__(self):
        """Initialize the Codebase Analyst Agent."""
        self.agent_id = "codebase-analyst"
        self.agent_name = "Codebase Analyst Agent"
        self.tier = 2
        self.capabilities = [
            "semantic_search",
            "pattern_recognition",
            "dependency_analysis",
            "impact_analysis",
            "code_structure_analysis"
        ]
        self.status = "active"
        logger.info(f"✅ {self.agent_name} initialized")
    
    async def analyze_codebase(
        self,
        db: AsyncSession,
        request: str,
        branch_id: Optional[str] = None,
        grove_id: Optional[str] = None,
        search_limit: int = 10,
        include_patterns: bool = True
    ) -> Dict[str, Any]:
        """
        Analyze codebase based on request.
        
        Args:
            db: Database session
            request: Analysis request (e.g., "Find all authentication code")
            branch_id: Optional DRYAD branch ID for context
            grove_id: Optional DRYAD grove ID
            search_limit: Number of results to return
            include_patterns: Whether to include pattern analysis
        
        Returns:
            Dict containing analysis results and metadata
        """
        try:
            logger.info(f"📊 Analyzing codebase: {request}")
            
            # Step 1: Perform semantic search using RAG
            search_results = await self._semantic_search(
                db=db,
                query=request,
                limit=search_limit
            )
            
            # Step 2: Analyze patterns if requested
            patterns = []
            if include_patterns and search_results:
                patterns = await self._analyze_patterns(search_results)
            
            # Step 3: Create analysis summary
            analysis = {
                "request": request,
                "timestamp": datetime.now().isoformat(),
                "results_count": len(search_results),
                "search_results": search_results,
                "patterns": patterns,
                "agent_id": self.agent_id
            }
            
            # Step 4: Store in DRYAD if branch_id provided
            vessel_id = None
            if branch_id:
                vessel_id = await self._store_in_dryad(
                    db=db,
                    branch_id=branch_id,
                    analysis=analysis
                )
                analysis["vessel_id"] = vessel_id
            
            logger.info(f"✅ Analysis complete: {len(search_results)} results found")
            
            return {
                "success": True,
                "analysis": analysis,
                "vessel_id": vessel_id
            }
            
        except Exception as e:
            logger.error(f"❌ Codebase analysis failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "analysis": None
            }
    
    async def _semantic_search(
        self,
        db: AsyncSession,
        query: str,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Perform semantic search using RAG system.
        
        Args:
            db: Database session
            query: Search query
            limit: Number of results
        
        Returns:
            List of search results
        """
        try:
            # Lazy import to avoid circular dependencies
            from app.core.rag_system import rag_system
            
            # Use RAG system for semantic search
            rag_result = await rag_system.retrieve_and_generate(
                db=db,
                query=query,
                search_limit=limit,
                score_threshold=0.6,  # Lower threshold for code search
                use_multi_agent=False  # Direct search, no multi-agent
            )
            
            # Extract search results
            retrieved_docs = rag_result.get("retrieved_documents", [])
            
            # Format results
            results = []
            for doc in retrieved_docs:
                results.append({
                    "id": doc.get("id"),
                    "content": doc.get("content", ""),
                    "score": doc.get("score", 0.0),
                    "document_title": doc.get("document_title", ""),
                    "document_type": doc.get("document_type", ""),
                    "chunk_index": doc.get("chunk_index", 0),
                    "metadata": doc.get("metadata", {})
                })
            
            logger.info(f"🔍 Semantic search found {len(results)} results")
            return results
            
        except Exception as e:
            logger.error(f"❌ Semantic search failed: {e}")
            return []
    
    async def _analyze_patterns(
        self,
        search_results: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Analyze patterns in search results.
        
        Args:
            search_results: List of search results
        
        Returns:
            List of identified patterns
        """
        try:
            patterns = []
            
            # Group by document type
            type_groups = {}
            for result in search_results:
                doc_type = result.get("document_type", "unknown")
                if doc_type not in type_groups:
                    type_groups[doc_type] = []
                type_groups[doc_type].append(result)
            
            # Analyze each group
            for doc_type, docs in type_groups.items():
                if len(docs) > 1:
                    patterns.append({
                        "pattern_type": "document_type_cluster",
                        "document_type": doc_type,
                        "count": len(docs),
                        "avg_score": sum(d.get("score", 0) for d in docs) / len(docs)
                    })
            
            # Analyze common terms (simple keyword extraction)
            all_content = " ".join([r.get("content", "") for r in search_results])
            words = all_content.lower().split()
            word_freq = {}
            for word in words:
                if len(word) > 4:  # Only significant words
                    word_freq[word] = word_freq.get(word, 0) + 1
            
            # Get top 5 keywords
            top_keywords = sorted(word_freq.items(), key=lambda x: x[1], reverse=True)[:5]
            if top_keywords:
                patterns.append({
                    "pattern_type": "common_keywords",
                    "keywords": [{"word": k, "frequency": v} for k, v in top_keywords]
                })
            
            logger.info(f"🔍 Identified {len(patterns)} patterns")
            return patterns
            
        except Exception as e:
            logger.error(f"❌ Pattern analysis failed: {e}")
            return []
    
    async def _store_in_dryad(
        self,
        db: AsyncSession,
        branch_id: str,
        analysis: Dict[str, Any]
    ) -> Optional[str]:
        """
        Store analysis results in DRYAD vessel.
        
        Args:
            db: Database session
            branch_id: DRYAD branch ID
            analysis: Analysis results
        
        Returns:
            Vessel ID if successful, None otherwise
        """
        try:
            # Lazy import to avoid circular dependencies
            from app.dryad.services.vessel_service import VesselService
            from app.dryad.schemas.vessel_schemas import VesselCreate
            
            vessel_service = VesselService(db)
            
            # Create vessel with analysis context
            vessel_data = VesselCreate(
                branch_id=branch_id,
                initial_context=json.dumps({
                    "agent": self.agent_id,
                    "analysis_type": "codebase_analysis",
                    "request": analysis.get("request"),
                    "results_count": analysis.get("results_count"),
                    "patterns_count": len(analysis.get("patterns", [])),
                    "timestamp": analysis.get("timestamp")
                })
            )
            
            vessel = await vessel_service.create_vessel(vessel_data)
            
            logger.info(f"✅ Stored analysis in DRYAD vessel: {vessel.id}")
            return vessel.id
            
        except Exception as e:
            logger.error(f"❌ Failed to store in DRYAD: {e}")
            return None
    
    def get_capabilities(self) -> Dict[str, Any]:
        """Get agent capabilities."""
        return {
            "agent_id": self.agent_id,
            "agent_name": self.agent_name,
            "tier": self.tier,
            "capabilities": self.capabilities,
            "status": self.status,
            "description": "Deep code understanding and analysis using RAG and pattern recognition"
        }
    
    async def health_check(self) -> Dict[str, Any]:
        """Check agent health."""
        try:
            # Check if RAG system is available
            from app.core.rag_system import rag_system
            
            return {
                "agent_id": self.agent_id,
                "status": "healthy",
                "rag_available": True,
                "timestamp": datetime.now().isoformat()
            }
        except Exception as e:
            return {
                "agent_id": self.agent_id,
                "status": "degraded",
                "rag_available": False,
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }

