"""
API endpoints for Codebase Analyst Agent
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime

from app.database.database import get_db
from app.services.codebase_analyst_agent import CodebaseAnalystAgent

router = APIRouter(prefix="/codebase-analyst", tags=["Codebase Analyst"])

# Initialize agent
codebase_analyst = CodebaseAnalystAgent()


# Request/Response Models
class CodebaseAnalysisRequest(BaseModel):
    """Request model for codebase analysis."""
    request: str = Field(..., description="Analysis request (e.g., 'Find all authentication code')")
    branch_id: Optional[str] = Field(None, description="DRYAD branch ID for context storage")
    grove_id: Optional[str] = Field(None, description="DRYAD grove ID")
    search_limit: int = Field(10, ge=1, le=50, description="Number of results to return")
    include_patterns: bool = Field(True, description="Whether to include pattern analysis")


class SearchResult(BaseModel):
    """Search result model."""
    id: str
    content: str
    score: float
    document_title: str
    document_type: str
    chunk_index: int
    metadata: Dict[str, Any]


class Pattern(BaseModel):
    """Pattern model."""
    pattern_type: str
    count: Optional[int] = None
    document_type: Optional[str] = None
    avg_score: Optional[float] = None
    keywords: Optional[List[Dict[str, Any]]] = None


class AnalysisResult(BaseModel):
    """Analysis result model."""
    request: str
    timestamp: str
    results_count: int
    search_results: List[SearchResult]
    patterns: List[Pattern]
    agent_id: str
    vessel_id: Optional[str] = None


class CodebaseAnalysisResponse(BaseModel):
    """Response model for codebase analysis."""
    success: bool
    analysis: Optional[AnalysisResult]
    vessel_id: Optional[str]
    error: Optional[str] = None


class CapabilitiesResponse(BaseModel):
    """Response model for agent capabilities."""
    agent_id: str
    agent_name: str
    tier: int
    capabilities: List[str]
    status: str
    description: str


class HealthCheckResponse(BaseModel):
    """Response model for health check."""
    agent_id: str
    status: str
    rag_available: bool
    timestamp: str
    error: Optional[str] = None


# Endpoints
@router.post("/analyze", response_model=CodebaseAnalysisResponse)
async def analyze_codebase(
    request: CodebaseAnalysisRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Analyze codebase based on request.
    
    This endpoint performs semantic code search using RAG and pattern analysis.
    Results can be stored in DRYAD for context tracking.
    
    **Example Request**:
    ```json
    {
        "request": "Find all authentication code",
        "branch_id": "branch-123",
        "search_limit": 10,
        "include_patterns": true
    }
    ```
    
    **Returns**:
    - Analysis results with search results and patterns
    - Vessel ID if stored in DRYAD
    """
    try:
        result = await codebase_analyst.analyze_codebase(
            db=db,
            request=request.request,
            branch_id=request.branch_id,
            grove_id=request.grove_id,
            search_limit=request.search_limit,
            include_patterns=request.include_patterns
        )
        
        return result
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")


@router.get("/capabilities", response_model=CapabilitiesResponse)
async def get_capabilities():
    """
    Get agent capabilities.
    
    Returns information about the Codebase Analyst Agent including:
    - Agent ID and name
    - Tier level
    - Available capabilities
    - Current status
    """
    return codebase_analyst.get_capabilities()


@router.get("/health", response_model=HealthCheckResponse)
async def health_check():
    """
    Check agent health.
    
    Returns the health status of the Codebase Analyst Agent including:
    - Overall status (healthy/degraded)
    - RAG system availability
    - Timestamp
    """
    return await codebase_analyst.health_check()


@router.post("/semantic-search")
async def semantic_search(
    query: str = Field(..., description="Search query"),
    limit: int = Field(10, ge=1, le=50, description="Number of results"),
    db: AsyncSession = Depends(get_db)
):
    """
    Perform semantic code search.
    
    This is a simplified endpoint that only performs semantic search
    without pattern analysis or DRYAD storage.
    
    **Parameters**:
    - query: Search query (e.g., "authentication functions")
    - limit: Number of results to return (1-50)
    
    **Returns**:
    - List of search results with relevance scores
    """
    try:
        results = await codebase_analyst._semantic_search(
            db=db,
            query=query,
            limit=limit
        )
        
        return {
            "success": True,
            "query": query,
            "results_count": len(results),
            "results": results
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Search failed: {str(e)}")


@router.post("/analyze-patterns")
async def analyze_patterns(
    search_results: List[SearchResult]
):
    """
    Analyze patterns in search results.
    
    This endpoint takes search results and identifies patterns such as:
    - Document type clusters
    - Common keywords
    - Frequency analysis
    
    **Parameters**:
    - search_results: List of search results to analyze
    
    **Returns**:
    - List of identified patterns
    """
    try:
        # Convert Pydantic models to dicts
        results_dicts = [r.dict() for r in search_results]
        
        patterns = await codebase_analyst._analyze_patterns(results_dicts)
        
        return {
            "success": True,
            "patterns_count": len(patterns),
            "patterns": patterns
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Pattern analysis failed: {str(e)}")

