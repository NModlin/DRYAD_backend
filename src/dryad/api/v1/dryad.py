# app/api/v1/endpoints/dryad.py
"""
Dryad API Endpoints

REST API endpoints for Dryad quantum-inspired knowledge tree system.
Provides CRUD operations for Groves, Branches, Vessels, and Oracle consultations.
"""

import logging
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional, List

from dryad.infrastructure.database import get_db
import app.core.security as security

# Import Dryad services
from dryad.services.grove_service import GroveService
from dryad.services.branch_service import BranchService
from dryad.services.vessel_service import VesselService
from dryad.services.oracle_service import OracleService
from dryad.services.multi_provider_service import MultiProviderService
from dryad.services.search_service import AdvancedSearchService
from dryad.services.suggestion_service import SuggestionService
from dryad.services.export_service import ExportService
from dryad.services.import_service import ImportService

# Import Dryad schemas
from dryad.schemas.grove_schemas import (
    GroveCreate,
    GroveUpdate,
    GroveResponse,
    GroveListOptions,
    GroveStats,
    GroveListResponse
)
from dryad.schemas.branch_schemas import (
    BranchCreate,
    BranchUpdate,
    BranchResponse,
    BranchTreeNode,
    BranchPath,
    BranchListResponse
)
from dryad.schemas.vessel_schemas import (
    VesselCreate,
    VesselResponse,
    VesselContentResponse,
    VesselContentUpdate,
    VesselSearchOptions,
    VesselSearchResponse
)
from dryad.schemas.dialogue_schemas import (
    ConsultationRequest,
    ConsultationResponse,
    ProcessResponseRequest,
    ProcessResponseResult,
    DialogueResponse,
    DialogueListResponse,
    ProviderInfo
)
from dryad.schemas.multi_provider_schemas import (
    MultiConsultRequest,
    MultiConsultResponse,
    ProviderSelectionRequest,
    ProviderSelectionResponse,
    ProviderHealthResponse,
    ProviderUsageResponse,
    FallbackChainConfig,
    FallbackChainResponse
)
from dryad.schemas.search_schemas import (
    AdvancedSearchRequest,
    AdvancedSearchResponse,
    SearchSuggestionRequest,
    SearchSuggestionResponse
)
from dryad.schemas.suggestion_schemas import (
    GenerateSuggestionsRequest,
    GenerateSuggestionsResponse,
    ListSuggestionsRequest,
    ListSuggestionsResponse,
    CreateBranchFromSuggestionRequest,
    CreateBranchFromSuggestionResponse,
    SuggestionAnalyticsRequest,
    SuggestionAnalyticsResponse,
    UpdateSuggestionRequest,
    DeleteSuggestionResponse,
    BranchSuggestion as BranchSuggestionSchema
)
from dryad.schemas.export_schemas import (
    ExportRequest,
    ExportResponse,
    ImportRequest,
    ImportResponse,
    ListFormatsResponse
)

# Import Dryad errors
from dryad.core.exceptions import DryadError

logger = logging.getLogger(__name__)
router = APIRouter()


# ============================================================================
# GROVE ENDPOINTS
# ============================================================================

@router.post("/groves", response_model=GroveResponse, status_code=201, tags=["Groves"])
async def create_grove(
    grove_data: GroveCreate,
    current_user: security.User = Depends(security.get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Create a new grove (knowledge tree workspace).
    
    A grove is a top-level container for organizing related branches of exploration.
    Each grove represents a distinct project, topic, or area of investigation.
    """
    try:
        service = GroveService(db)
        grove = await service.create_grove(grove_data)
        logger.info(f"Grove created: {grove.id} by user {current_user.id}")
        return grove
    except DryadError as e:
        logger.error(f"Dryad error creating grove: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error creating grove: {e}")
        raise HTTPException(status_code=500, detail="Failed to create grove")


@router.get("/groves", response_model=GroveListResponse, tags=["Groves"])
async def list_groves(
    include_archived: bool = Query(False, description="Include archived groves"),
    favorites_only: bool = Query(False, description="Show only favorite groves"),
    sort_by: str = Query("last_accessed_at", description="Sort field"),
    sort_order: str = Query("DESC", description="Sort order (ASC/DESC)"),
    limit: Optional[int] = Query(None, ge=1, le=1000, description="Maximum results"),
    offset: Optional[int] = Query(None, ge=0, description="Results to skip"),
    current_user: security.User = Depends(security.get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    List all groves with filtering and sorting options.
    
    Returns a paginated list of groves accessible to the current user.
    """
    try:
        service = GroveService(db)
        options = GroveListOptions(
            include_archived=include_archived,
            favorites_only=favorites_only,
            sort_by=sort_by,
            sort_order=sort_order,
            limit=limit,
            offset=offset
        )
        groves = await service.list_groves(options)
        total = len(groves)
        
        return GroveListResponse(
            groves=groves,
            total=total,
            limit=limit,
            offset=offset
        )
    except DryadError as e:
        logger.error(f"Dryad error listing groves: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error listing groves: {e}")
        raise HTTPException(status_code=500, detail="Failed to list groves")


@router.get("/groves/{grove_id}", response_model=GroveResponse, tags=["Groves"])
async def get_grove(
    grove_id: str,
    current_user: security.User = Depends(security.get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get a specific grove by ID.
    
    Returns detailed information about a grove including metadata and statistics.
    """
    try:
        service = GroveService(db)
        grove = await service.get_grove_by_id(grove_id)
        
        if not grove:
            raise HTTPException(status_code=404, detail=f"Grove not found: {grove_id}")
        
        return grove
    except HTTPException:
        raise
    except DryadError as e:
        logger.error(f"Dryad error getting grove: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error getting grove: {e}")
        raise HTTPException(status_code=500, detail="Failed to get grove")


@router.put("/groves/{grove_id}", response_model=GroveResponse, tags=["Groves"])
async def update_grove(
    grove_id: str,
    grove_data: GroveUpdate,
    current_user: security.User = Depends(security.get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Update an existing grove.
    
    Allows updating grove name, description, metadata, and favorite status.
    """
    try:
        service = GroveService(db)
        grove = await service.update_grove(grove_id, grove_data)
        logger.info(f"Grove updated: {grove_id} by user {current_user.id}")
        return grove
    except DryadError as e:
        logger.error(f"Dryad error updating grove: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error updating grove: {e}")
        raise HTTPException(status_code=500, detail="Failed to update grove")


@router.delete("/groves/{grove_id}", status_code=204, tags=["Groves"])
async def delete_grove(
    grove_id: str,
    current_user: security.User = Depends(security.get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Delete a grove and all its branches.
    
    WARNING: This operation is irreversible and will delete all branches,
    vessels, and dialogues associated with this grove.
    """
    try:
        service = GroveService(db)
        await service.delete_grove(grove_id)
        logger.info(f"Grove deleted: {grove_id} by user {current_user.id}")
        return None
    except DryadError as e:
        logger.error(f"Dryad error deleting grove: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error deleting grove: {e}")
        raise HTTPException(status_code=500, detail="Failed to delete grove")


@router.get("/groves/{grove_id}/stats", response_model=GroveStats, tags=["Groves"])
async def get_grove_stats(
    grove_id: str,
    current_user: security.User = Depends(security.get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get statistics for a grove.
    
    Returns counts of branches, observation points, and other metrics.
    """
    try:
        service = GroveService(db)
        stats = await service.get_grove_stats(grove_id)
        return stats
    except DryadError as e:
        logger.error(f"Dryad error getting grove stats: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error getting grove stats: {e}")
        raise HTTPException(status_code=500, detail="Failed to get grove statistics")


@router.post("/groves/{grove_id}/favorite", response_model=GroveResponse, tags=["Groves"])
async def toggle_grove_favorite(
    grove_id: str,
    current_user: security.User = Depends(security.get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Toggle grove favorite status.

    Marks or unmarks a grove as a favorite for quick access.
    """
    try:
        service = GroveService(db)
        grove = await service.toggle_favorite(grove_id)
        logger.info(f"Grove favorite toggled: {grove_id} by user {current_user.id}")
        return grove
    except DryadError as e:
        logger.error(f"Dryad error toggling favorite: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error toggling favorite: {e}")
        raise HTTPException(status_code=500, detail="Failed to toggle favorite")


# ============================================================================
# BRANCH ENDPOINTS
# ============================================================================

@router.post("/branches", response_model=BranchResponse, status_code=201, tags=["Branches"])
async def create_branch(
    branch_data: BranchCreate,
    current_user: security.User = Depends(security.get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Create a new branch in a grove.

    A branch represents a specific path of exploration within a grove.
    Branches can have parent-child relationships forming a tree structure.
    """
    try:
        service = BranchService(db)
        branch = await service.create_branch(branch_data)
        logger.info(f"Branch created: {branch.id} in grove {branch_data.grove_id} by user {current_user.id}")
        return branch
    except DryadError as e:
        logger.error(f"Dryad error creating branch: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error creating branch: {e}")
        raise HTTPException(status_code=500, detail="Failed to create branch")


@router.get("/branches/{branch_id}", response_model=BranchResponse, tags=["Branches"])
async def get_branch(
    branch_id: str,
    current_user: security.User = Depends(security.get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get a specific branch by ID.

    Returns detailed information about a branch including its position in the tree.
    """
    try:
        service = BranchService(db)
        branch = await service.get_branch_by_id(branch_id)

        if not branch:
            raise HTTPException(status_code=404, detail=f"Branch not found: {branch_id}")

        return branch
    except HTTPException:
        raise
    except DryadError as e:
        logger.error(f"Dryad error getting branch: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error getting branch: {e}")
        raise HTTPException(status_code=500, detail="Failed to get branch")


@router.put("/branches/{branch_id}", response_model=BranchResponse, tags=["Branches"])
async def update_branch(
    branch_id: str,
    branch_data: BranchUpdate,
    current_user: security.User = Depends(security.get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Update an existing branch.

    Allows updating branch name, description, status, and priority.
    """
    try:
        service = BranchService(db)
        branch = await service.update_branch(branch_id, branch_data)
        logger.info(f"Branch updated: {branch_id} by user {current_user.id}")
        return branch
    except DryadError as e:
        logger.error(f"Dryad error updating branch: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error updating branch: {e}")
        raise HTTPException(status_code=500, detail="Failed to update branch")


@router.delete("/branches/{branch_id}", status_code=204, tags=["Branches"])
async def delete_branch(
    branch_id: str,
    current_user: security.User = Depends(security.get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Delete a branch and all its descendants.

    WARNING: This operation is irreversible and will delete all child branches
    and their associated vessels and dialogues.
    """
    try:
        service = BranchService(db)
        await service.delete_branch(branch_id)
        logger.info(f"Branch deleted: {branch_id} by user {current_user.id}")
        return None
    except DryadError as e:
        logger.error(f"Dryad error deleting branch: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error deleting branch: {e}")
        raise HTTPException(status_code=500, detail="Failed to delete branch")


@router.get("/groves/{grove_id}/branches", response_model=BranchListResponse, tags=["Branches"])
async def list_grove_branches(
    grove_id: str,
    current_user: security.User = Depends(security.get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    List all branches in a grove.

    Returns a flat list of all branches in the grove.
    """
    try:
        service = BranchService(db)
        branches = await service.get_branches_by_grove(grove_id)

        return BranchListResponse(
            branches=branches,
            total=len(branches)
        )
    except DryadError as e:
        logger.error(f"Dryad error listing branches: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error listing branches: {e}")
        raise HTTPException(status_code=500, detail="Failed to list branches")


@router.get("/groves/{grove_id}/tree", response_model=Optional[BranchTreeNode], tags=["Branches"])
async def get_grove_tree(
    grove_id: str,
    current_user: security.User = Depends(security.get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get the complete branch tree for a grove.

    Returns a hierarchical tree structure showing all branches and their relationships.
    """
    try:
        service = BranchService(db)
        tree = await service.build_branch_tree(grove_id)
        return tree
    except DryadError as e:
        logger.error(f"Dryad error building tree: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error building tree: {e}")
        raise HTTPException(status_code=500, detail="Failed to build branch tree")


@router.get("/branches/{branch_id}/path", response_model=BranchPath, tags=["Branches"])
async def get_branch_path(
    branch_id: str,
    current_user: security.User = Depends(security.get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get the path from root to a specific branch.

    Returns an ordered list of branches from the root to the specified branch.
    """
    try:
        service = BranchService(db)
        path = await service.get_branch_path(branch_id)
        return path
    except DryadError as e:
        logger.error(f"Dryad error getting path: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error getting path: {e}")
        raise HTTPException(status_code=500, detail="Failed to get branch path")


@router.get("/branches/{branch_id}/children", response_model=BranchListResponse, tags=["Branches"])
async def get_branch_children(
    branch_id: str,
    current_user: security.User = Depends(security.get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get all child branches of a specific branch.

    Returns immediate children only (not descendants).
    """
    try:
        service = BranchService(db)
        children = await service.get_child_branches(branch_id)

        return BranchListResponse(
            branches=children,
            total=len(children)
        )
    except DryadError as e:
        logger.error(f"Dryad error getting children: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error getting children: {e}")
        raise HTTPException(status_code=500, detail="Failed to get child branches")


@router.post("/branches/{branch_id}/archive", response_model=BranchResponse, tags=["Branches"])
async def archive_branch(
    branch_id: str,
    current_user: security.User = Depends(security.get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Archive a branch.

    Archived branches are hidden from normal views but can be restored.
    """
    try:
        service = BranchService(db)
        branch = await service.archive_branch(branch_id)
        logger.info(f"Branch archived: {branch_id} by user {current_user.id}")
        return branch
    except DryadError as e:
        logger.error(f"Dryad error archiving branch: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error archiving branch: {e}")
        raise HTTPException(status_code=500, detail="Failed to archive branch")


@router.post("/branches/{branch_id}/activate", response_model=BranchResponse, tags=["Branches"])
async def activate_branch(
    branch_id: str,
    current_user: security.User = Depends(security.get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Activate an archived branch.

    Restores a branch to active status.
    """
    try:
        service = BranchService(db)
        branch = await service.activate_branch(branch_id)
        logger.info(f"Branch activated: {branch_id} by user {current_user.id}")
        return branch
    except DryadError as e:
        logger.error(f"Dryad error activating branch: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error activating branch: {e}")
        raise HTTPException(status_code=500, detail="Failed to activate branch")


# ============================================================================
# VESSEL ENDPOINTS
# ============================================================================

@router.post("/vessels", response_model=VesselResponse, status_code=201, tags=["Vessels"])
async def create_vessel(
    vessel_data: VesselCreate,
    current_user: security.User = Depends(security.get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Create a new vessel for a branch.

    A vessel is a context container that stores the state and knowledge
    accumulated along a branch's exploration path.
    """
    try:
        service = VesselService(db)
        vessel = await service.create_vessel(vessel_data)
        logger.info(f"Vessel created: {vessel.id} for branch {vessel_data.branch_id} by user {current_user.id}")
        return vessel
    except DryadError as e:
        logger.error(f"Dryad error creating vessel: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error creating vessel: {e}")
        raise HTTPException(status_code=500, detail="Failed to create vessel")


@router.get("/vessels/search", response_model=VesselSearchResponse, tags=["Vessels"])
async def search_vessels(
    query: str = Query(..., min_length=1, description="Search query"),
    grove_id: Optional[str] = Query(None, description="Limit to specific grove"),
    include_archived: bool = Query(False, description="Include archived vessels"),
    limit: int = Query(10, ge=1, le=100, description="Maximum results"),
    current_user: security.User = Depends(security.get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Search vessels by content.

    Performs semantic search across vessel content to find relevant knowledge.
    """
    try:
        service = VesselService(db)
        options = VesselSearchOptions(
            grove_id=grove_id,
            include_archived=include_archived,
            limit=limit
        )
        results = await service.search_vessels(query, options)

        return VesselSearchResponse(
            results=results,
            total=len(results),
            query=query,
            execution_time=0.0  # TODO: Add timing
        )
    except DryadError as e:
        logger.error(f"Dryad error searching vessels: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error searching vessels: {e}")
        raise HTTPException(status_code=500, detail="Failed to search vessels")


@router.get("/vessels/{vessel_id}", response_model=VesselResponse, tags=["Vessels"])
async def get_vessel(
    vessel_id: str,
    current_user: security.User = Depends(security.get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get a specific vessel by ID.

    Returns vessel metadata and storage information.
    """
    try:
        service = VesselService(db)
        vessel = await service.get_vessel_by_id(vessel_id)

        if not vessel:
            raise HTTPException(status_code=404, detail=f"Vessel not found: {vessel_id}")

        return vessel
    except HTTPException:
        raise
    except DryadError as e:
        logger.error(f"Dryad error getting vessel: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error getting vessel: {e}")
        raise HTTPException(status_code=500, detail="Failed to get vessel")


@router.get("/branches/{branch_id}/vessel", response_model=VesselResponse, tags=["Vessels"])
async def get_branch_vessel(
    branch_id: str,
    current_user: security.User = Depends(security.get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get the vessel for a specific branch.

    Each branch has one vessel that stores its context.
    """
    try:
        service = VesselService(db)
        vessel = await service.get_vessel_by_branch_id(branch_id)

        if not vessel:
            raise HTTPException(status_code=404, detail=f"Vessel not found for branch: {branch_id}")

        return vessel
    except HTTPException:
        raise
    except DryadError as e:
        logger.error(f"Dryad error getting vessel: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error getting vessel: {e}")
        raise HTTPException(status_code=500, detail="Failed to get vessel")


@router.get("/vessels/{vessel_id}/content", response_model=VesselContentResponse, tags=["Vessels"])
async def get_vessel_content(
    vessel_id: str,
    current_user: security.User = Depends(security.get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get the full content of a vessel.

    Returns all context, summaries, and dialogue history stored in the vessel.
    """
    try:
        service = VesselService(db)
        content = await service.get_vessel_content(vessel_id)
        return content
    except DryadError as e:
        logger.error(f"Dryad error getting vessel content: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error getting vessel content: {e}")
        raise HTTPException(status_code=500, detail="Failed to get vessel content")


@router.put("/vessels/{vessel_id}/content", status_code=204, tags=["Vessels"])
async def update_vessel_content(
    vessel_id: str,
    content_update: VesselContentUpdate,
    current_user: security.User = Depends(security.get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Update vessel content.

    Allows updating the summary, context, and metadata stored in a vessel.
    """
    try:
        service = VesselService(db)
        await service.update_vessel_content(vessel_id, content_update)
        logger.info(f"Vessel content updated: {vessel_id} by user {current_user.id}")
        return None
    except DryadError as e:
        logger.error(f"Dryad error updating vessel content: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error updating vessel content: {e}")
        raise HTTPException(status_code=500, detail="Failed to update vessel content")


@router.delete("/vessels/{vessel_id}", status_code=204, tags=["Vessels"])
async def delete_vessel(
    vessel_id: str,
    current_user: security.User = Depends(security.get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Delete a vessel.

    WARNING: This operation is irreversible.
    """
    try:
        service = VesselService(db)
        await service.delete_vessel(vessel_id)
        logger.info(f"Vessel deleted: {vessel_id} by user {current_user.id}")
        return None
    except DryadError as e:
        logger.error(f"Dryad error deleting vessel: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error deleting vessel: {e}")
        raise HTTPException(status_code=500, detail="Failed to delete vessel")


# ============================================================================
# ORACLE ENDPOINTS
# ============================================================================

@router.get("/oracle/providers", response_model=List[ProviderInfo], tags=["Oracle"])
async def list_oracle_providers(
    current_user: security.User = Depends(security.get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    List all available oracle providers.

    Returns information about AI providers that can be consulted for guidance.
    """
    try:
        service = OracleService(db)
        providers = await service.get_providers()
        return providers
    except DryadError as e:
        logger.error(f"Dryad error listing providers: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error listing providers: {e}")
        raise HTTPException(status_code=500, detail="Failed to list oracle providers")


@router.get("/oracle/providers/health", response_model=ProviderHealthResponse, tags=["Multi-Provider Oracle"])
async def get_provider_health(
    current_user: security.User = Depends(security.get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get health status of all providers.

    Returns health metrics including status, response times, error rates, and availability.
    """
    try:
        multi_provider_service = MultiProviderService(db)
        return await multi_provider_service.get_provider_health()
    except DryadError as e:
        logger.error(f"Dryad error getting provider health: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error getting provider health: {e}")
        raise HTTPException(status_code=500, detail="Failed to get provider health")


@router.get("/oracle/providers/usage", response_model=ProviderUsageResponse, tags=["Multi-Provider Oracle"])
async def get_provider_usage(
    period_start: Optional[str] = Query(None, description="Start of period (ISO format)"),
    period_end: Optional[str] = Query(None, description="End of period (ISO format)"),
    current_user: security.User = Depends(security.get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get provider usage statistics.

    Returns usage metrics including request counts, token usage, costs, and success rates
    for the specified time period.
    """
    try:
        multi_provider_service = MultiProviderService(db)
        return await multi_provider_service.get_provider_usage(period_start, period_end)
    except DryadError as e:
        logger.error(f"Dryad error getting provider usage: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error getting provider usage: {e}")
        raise HTTPException(status_code=500, detail="Failed to get provider usage")


@router.get("/oracle/providers/{provider_id}", response_model=ProviderInfo, tags=["Oracle"])
async def get_oracle_provider(
    provider_id: str,
    current_user: security.User = Depends(security.get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get information about a specific oracle provider.
    """
    try:
        service = OracleService(db)
        provider = await service.get_provider(provider_id)

        if not provider:
            raise HTTPException(status_code=404, detail=f"Provider not found: {provider_id}")

        return provider
    except HTTPException:
        raise
    except DryadError as e:
        logger.error(f"Dryad error getting provider: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error getting provider: {e}")
        raise HTTPException(status_code=500, detail="Failed to get oracle provider")


@router.post("/oracle/consult", response_model=ProcessResponseResult, tags=["Oracle"])
async def consult_oracle(
    request: ConsultationRequest,
    current_user: security.User = Depends(security.get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Consult an oracle for guidance.

    Sends a query to an AI provider and processes the response,
    extracting insights and creating a dialogue record.
    """
    try:
        service = OracleService(db)
        result = await service.consult_oracle(request)
        logger.info(f"Oracle consultation completed for branch {request.branch_id} by user {current_user.id}")
        return result
    except DryadError as e:
        logger.error(f"Dryad error consulting oracle: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error consulting oracle: {e}")
        raise HTTPException(status_code=500, detail="Failed to consult oracle")


@router.post("/oracle/prepare", response_model=ConsultationResponse, tags=["Oracle"])
async def prepare_consultation(
    request: ConsultationRequest,
    current_user: security.User = Depends(security.get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Prepare a consultation prompt without executing it.

    Returns the formatted prompt that would be sent to the oracle,
    useful for review before actual consultation.
    """
    try:
        service = OracleService(db)
        response = await service.prepare_consultation(request)
        return response
    except DryadError as e:
        logger.error(f"Dryad error preparing consultation: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error preparing consultation: {e}")
        raise HTTPException(status_code=500, detail="Failed to prepare consultation")


@router.post("/oracle/process", response_model=ProcessResponseResult, tags=["Oracle"])
async def process_oracle_response(
    request: ProcessResponseRequest,
    current_user: security.User = Depends(security.get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Process a raw oracle response.

    Useful when you have an oracle response from an external source
    and want to process it through Dryad's wisdom extraction system.
    """
    try:
        service = OracleService(db)
        result = await service.process_response(request)
        logger.info(f"Oracle response processed for branch {request.branch_id} by user {current_user.id}")
        return result
    except DryadError as e:
        logger.error(f"Dryad error processing response: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error processing response: {e}")
        raise HTTPException(status_code=500, detail="Failed to process oracle response")


# ============================================================================
# DIALOGUE ENDPOINTS
# ============================================================================

@router.get("/branches/{branch_id}/dialogues", response_model=DialogueListResponse, tags=["Dialogues"])
async def list_branch_dialogues(
    branch_id: str,
    current_user: security.User = Depends(security.get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    List all dialogues for a branch.

    Returns all oracle consultations and their insights for a specific branch.
    """
    try:
        service = OracleService(db)
        dialogues = await service.get_dialogues(branch_id)

        return DialogueListResponse(
            dialogues=dialogues,
            total=len(dialogues),
            branch_id=branch_id
        )
    except DryadError as e:
        logger.error(f"Dryad error listing dialogues: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error listing dialogues: {e}")
        raise HTTPException(status_code=500, detail="Failed to list dialogues")


@router.get("/dialogues/{dialogue_id}", response_model=DialogueResponse, tags=["Dialogues"])
async def get_dialogue(
    dialogue_id: str,
    current_user: security.User = Depends(security.get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get a specific dialogue by ID.

    Returns the complete dialogue including all messages and extracted insights.
    """
    try:
        service = OracleService(db)
        dialogue = await service.get_dialogue(dialogue_id)

        if not dialogue:
            raise HTTPException(status_code=404, detail=f"Dialogue not found: {dialogue_id}")

        return dialogue
    except HTTPException:
        raise
    except DryadError as e:
        logger.error(f"Dryad error getting dialogue: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error getting dialogue: {e}")
        raise HTTPException(status_code=500, detail="Failed to get dialogue")


@router.delete("/dialogues/{dialogue_id}", status_code=204, tags=["Dialogues"])
async def delete_dialogue(
    dialogue_id: str,
    current_user: security.User = Depends(security.get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Delete a dialogue.

    Removes a dialogue and all its messages from the system.
    """
    try:
        service = OracleService(db)
        await service.delete_dialogue(dialogue_id)
        logger.info(f"Dialogue deleted: {dialogue_id} by user {current_user.id}")
        return None
    except DryadError as e:
        logger.error(f"Dryad error deleting dialogue: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error deleting dialogue: {e}")
        raise HTTPException(status_code=500, detail="Failed to delete dialogue")


# ============================================================================
# MULTI-PROVIDER ORACLE ENDPOINTS
# ============================================================================

@router.post("/oracle/multi-consult", response_model=MultiConsultResponse, tags=["Multi-Provider Oracle"])
async def multi_provider_consult(
    request: MultiConsultRequest,
    current_user: security.User = Depends(security.get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Consult multiple oracle providers and return consensus result.

    Queries multiple AI providers concurrently and applies a consensus strategy
    to combine their responses into a single high-confidence answer.
    """
    try:
        service = MultiProviderService(db)
        result = await service.multi_consult(request)
        logger.info(f"Multi-consult completed with {len(result.consensus.providers_used)} providers")
        return result
    except DryadError as e:
        logger.error(f"Dryad error in multi-consult: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error in multi-consult: {e}")
        raise HTTPException(status_code=500, detail="Failed to complete multi-provider consultation")


@router.post("/oracle/providers/select", response_model=ProviderSelectionResponse, tags=["Multi-Provider Oracle"])
async def select_provider(
    request: ProviderSelectionRequest,
    current_user: security.User = Depends(security.get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Intelligently select the best provider for a query.

    Analyzes query requirements and provider capabilities to select
    the optimal provider based on speed, quality, cost, and availability.
    """
    try:
        service = MultiProviderService(db)
        result = await service.select_provider(request)
        logger.info(f"Selected provider: {result.provider_id} ({result.reason})")
        return result
    except DryadError as e:
        logger.error(f"Dryad error selecting provider: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error selecting provider: {e}")
        raise HTTPException(status_code=500, detail="Failed to select provider")


@router.post("/oracle/fallback-chain", response_model=FallbackChainResponse, tags=["Multi-Provider Oracle"])
async def execute_fallback_chain(
    chain_config: FallbackChainConfig,
    branch_id: str = Query(..., description="Branch ID for consultation"),
    query: str = Query(..., description="Query to send to providers"),
    current_user: security.User = Depends(security.get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Execute a fallback chain of providers.

    Tries providers in sequence until one succeeds, implementing
    automatic failover for high availability.
    """
    try:
        service = MultiProviderService(db)
        result = await service.execute_fallback_chain(chain_config, branch_id, query)
        logger.info(f"Fallback chain succeeded with provider: {result.successful_provider_id}")
        return result
    except DryadError as e:
        logger.error(f"Dryad error in fallback chain: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error in fallback chain: {e}")
        raise HTTPException(status_code=500, detail="Failed to execute fallback chain")


# ============================================================================
# SEARCH ENDPOINTS
# ============================================================================

@router.post("/search", response_model=AdvancedSearchResponse, tags=["Search"])
async def advanced_search(
    request: AdvancedSearchRequest,
    current_user: security.User = Depends(security.get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Perform advanced search across Dryad knowledge system.

    Supports semantic (vector), keyword, and hybrid search across vessels,
    dialogues, and branches with faceted filtering and relevance ranking.
    """
    try:
        service = AdvancedSearchService(db)
        result = await service.search(request, str(current_user.id))
        logger.info(f"Search completed: '{request.query}' - {result.total} results in {result.execution_time:.2f}s")
        return result
    except DryadError as e:
        logger.error(f"Dryad error in search: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error in search: {e}")
        raise HTTPException(status_code=500, detail="Failed to perform search")


@router.get("/search/suggestions", response_model=SearchSuggestionResponse, tags=["Search"])
async def get_search_suggestions(
    query: str = Query(..., min_length=1, description="Partial search query"),
    scope: str = Query("all", description="Search scope (vessels, dialogues, branches, all)"),
    limit: int = Query(5, ge=1, le=20, description="Maximum suggestions"),
    current_user: security.User = Depends(security.get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get search suggestions based on partial query.

    Provides autocomplete suggestions to help users formulate better searches.
    """
    try:
        from dryad.schemas.search_schemas import SearchScope

        service = AdvancedSearchService(db)
        request = SearchSuggestionRequest(
            query=query,
            scope=SearchScope(scope),
            limit=limit
        )
        result = await service.get_suggestions(request)
        logger.debug(f"Generated {len(result.suggestions)} suggestions for '{query}'")
        return result
    except DryadError as e:
        logger.error(f"Dryad error getting suggestions: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error getting suggestions: {e}")
        raise HTTPException(status_code=500, detail="Failed to get search suggestions")


# ============================================================================
# BRANCH SUGGESTION ENDPOINTS
# ============================================================================

@router.post("/suggestions/generate", response_model=GenerateSuggestionsResponse, tags=["Suggestions"])
async def generate_branch_suggestions(
    request: GenerateSuggestionsRequest,
    current_user: security.User = Depends(security.get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Generate AI-powered branch suggestions from oracle dialogue.

    Analyzes oracle wisdom (themes, questions, decisions, facts) and generates
    intelligent branch suggestions with priority scoring and auto-creation.
    """
    try:
        service = SuggestionService(db)
        result = await service.generate_suggestions(request, str(current_user.id))
        logger.info(f"Generated {result.total_suggestions} suggestions for dialogue {request.dialogue_id}")
        return result
    except DryadError as e:
        logger.error(f"Dryad error generating suggestions: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error generating suggestions: {e}")
        raise HTTPException(status_code=500, detail="Failed to generate branch suggestions")


@router.post("/suggestions/list", response_model=ListSuggestionsResponse, tags=["Suggestions"])
async def list_branch_suggestions(
    request: ListSuggestionsRequest,
    current_user: security.User = Depends(security.get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    List branch suggestions with filters.

    Supports filtering by branch, dialogue, type, priority, and more.
    """
    try:
        service = SuggestionService(db)
        result = await service.list_suggestions(request)
        logger.debug(f"Listed {len(result.suggestions)} suggestions (total: {result.total})")
        return result
    except DryadError as e:
        logger.error(f"Dryad error listing suggestions: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error listing suggestions: {e}")
        raise HTTPException(status_code=500, detail="Failed to list branch suggestions")


@router.get("/suggestions/{suggestion_id}", response_model=BranchSuggestionSchema, tags=["Suggestions"])
async def get_branch_suggestion(
    suggestion_id: str,
    current_user: security.User = Depends(security.get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get a specific branch suggestion by ID.
    """
    try:
        service = SuggestionService(db)
        result = await service.get_suggestion_by_id(suggestion_id)
        return result
    except DryadError as e:
        logger.error(f"Dryad error getting suggestion: {e}")
        raise HTTPException(status_code=404 if "not found" in str(e).lower() else 400, detail=str(e))
    except Exception as e:
        logger.error(f"Error getting suggestion: {e}")
        raise HTTPException(status_code=500, detail="Failed to get branch suggestion")


@router.post("/suggestions/{suggestion_id}/create-branch", response_model=CreateBranchFromSuggestionResponse, tags=["Suggestions"])
async def create_branch_from_suggestion(
    suggestion_id: str,
    request: CreateBranchFromSuggestionRequest,
    current_user: security.User = Depends(security.get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Create a branch from a suggestion.

    Converts a suggestion into an actual branch in the knowledge tree.
    """
    try:
        # Ensure suggestion_id matches
        if request.suggestion_id != suggestion_id:
            raise HTTPException(status_code=400, detail="Suggestion ID mismatch")

        service = SuggestionService(db)
        result = await service.create_branch_from_suggestion(request, str(current_user.id))
        logger.info(f"Created branch {result.branch_id} from suggestion {suggestion_id}")
        return result
    except DryadError as e:
        logger.error(f"Dryad error creating branch from suggestion: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error creating branch from suggestion: {e}")
        raise HTTPException(status_code=500, detail="Failed to create branch from suggestion")


@router.put("/suggestions/{suggestion_id}", response_model=BranchSuggestionSchema, tags=["Suggestions"])
async def update_branch_suggestion(
    suggestion_id: str,
    request: UpdateSuggestionRequest,
    current_user: security.User = Depends(security.get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Update a branch suggestion.

    Allows modifying title, description, priority, keywords, and metadata.
    """
    try:
        service = SuggestionService(db)
        result = await service.update_suggestion(suggestion_id, request)
        logger.info(f"Updated suggestion {suggestion_id}")
        return result
    except DryadError as e:
        logger.error(f"Dryad error updating suggestion: {e}")
        raise HTTPException(status_code=404 if "not found" in str(e).lower() else 400, detail=str(e))
    except Exception as e:
        logger.error(f"Error updating suggestion: {e}")
        raise HTTPException(status_code=500, detail="Failed to update branch suggestion")


@router.delete("/suggestions/{suggestion_id}", response_model=DeleteSuggestionResponse, tags=["Suggestions"])
async def delete_branch_suggestion(
    suggestion_id: str,
    reason: Optional[str] = Query(None, description="Reason for deletion"),
    current_user: security.User = Depends(security.get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Delete a branch suggestion.
    """
    try:
        service = SuggestionService(db)
        result = await service.delete_suggestion(suggestion_id, reason)
        logger.info(f"Deleted suggestion {suggestion_id}")
        return result
    except DryadError as e:
        logger.error(f"Dryad error deleting suggestion: {e}")
        raise HTTPException(status_code=404 if "not found" in str(e).lower() else 400, detail=str(e))
    except Exception as e:
        logger.error(f"Error deleting suggestion: {e}")
        raise HTTPException(status_code=500, detail="Failed to delete branch suggestion")


@router.post("/suggestions/analytics", response_model=SuggestionAnalyticsResponse, tags=["Suggestions"])
async def get_suggestion_analytics(
    request: SuggestionAnalyticsRequest,
    current_user: security.User = Depends(security.get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get analytics for branch suggestions.

    Provides insights into suggestion generation, auto-creation rates,
    priority distribution, and top keywords.
    """
    try:
        service = SuggestionService(db)
        result = await service.get_suggestion_analytics(request)
        logger.debug(f"Generated analytics: {result.analytics.total_suggestions} total suggestions")
        return result
    except DryadError as e:
        logger.error(f"Dryad error getting analytics: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error getting analytics: {e}")
        raise HTTPException(status_code=500, detail="Failed to get suggestion analytics")


# ============================================================================
# EXPORT/IMPORT ENDPOINTS
# ============================================================================

@router.post("/groves/{grove_id}/export", response_model=ExportResponse, tags=["Export/Import"])
async def export_grove(
    grove_id: str,
    request: ExportRequest,
    current_user: security.User = Depends(security.get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Export a grove to specified format.

    Exports the entire grove structure including branches, vessels, dialogues,
    and related entities to JSON, YAML, or Markdown format.

    **Features:**
    - Multi-format export (JSON, YAML, Markdown)
    - Selective export with filters
    - Tree structure preservation
    - Metadata handling
    - Optional compression

    **Export Formats:**
    - **JSON**: Structured, machine-readable format
    - **YAML**: Human-friendly, structured format
    - **Markdown**: Highly readable, documentation-friendly format

    **Export Scopes:**
    - **FULL**: Export everything (branches, vessels, dialogues, suggestions)
    - **BRANCHES_ONLY**: Export branches without vessels/dialogues
    - **METADATA_ONLY**: Export only metadata, no content

    **Filters:**
    - Branch IDs: Export specific branches
    - Include archived: Include/exclude archived branches
    - Min priority: Minimum branch priority
    - Date range: Created after/before dates
    - Max depth: Maximum branch depth
    """
    try:
        # Update request with grove_id
        request.grove_id = grove_id

        service = ExportService(db)
        result = await service.export_grove(request, current_user.id)
        logger.info(f"Exported grove {grove_id}: {result.metadata.total_branches} branches")
        return result
    except DryadError as e:
        logger.error(f"Dryad error exporting grove: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error exporting grove: {e}")
        raise HTTPException(status_code=500, detail="Failed to export grove")


@router.post("/groves/import", response_model=ImportResponse, tags=["Export/Import"])
async def import_grove(
    request: ImportRequest,
    current_user: security.User = Depends(security.get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Import a grove from specified format.

    Imports a grove structure from JSON, YAML, or Markdown format with
    various merge strategies and validation options.

    **Features:**
    - Multi-format import (JSON, YAML, Markdown)
    - Import strategies (create new, merge, skip duplicates, overwrite)
    - Validation before import
    - ID and timestamp preservation options
    - Selective import (vessels, dialogues, suggestions, observation points)

    **Import Strategies:**
    - **CREATE_NEW**: Create new grove with new IDs
    - **MERGE_EXISTING**: Merge into existing grove (requires target_grove_id)
    - **SKIP_DUPLICATES**: Skip items that already exist
    - **OVERWRITE**: Overwrite existing items

    **Import Options:**
    - **validate_only**: Only validate, don't import
    - **skip_validation**: Skip validation (dangerous)
    - **preserve_ids**: Preserve original IDs
    - **preserve_timestamps**: Preserve original timestamps
    - **import_vessel_content**: Import vessel file content
    - **import_dialogue_messages**: Import dialogue messages
    - **import_suggestions**: Import branch suggestions
    - **import_observation_points**: Import observation points

    **Validation:**
    - Version compatibility check
    - Required fields validation
    - Strategy-specific validation
    - Total items count
    """
    try:
        service = ImportService(db)
        result = await service.import_grove(request, current_user.id)

        if result.success:
            logger.info(f"Imported grove {result.grove_id}: {result.stats.branches_created} branches created")
        else:
            logger.warning(f"Import failed: {len(result.errors)} errors")

        return result
    except DryadError as e:
        logger.error(f"Dryad error importing grove: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error importing grove: {e}")
        raise HTTPException(status_code=500, detail="Failed to import grove")


@router.get("/export/formats", response_model=ListFormatsResponse, tags=["Export/Import"])
async def list_export_formats(
    current_user: security.User = Depends(security.get_current_user)
):
    """
    List available export formats.

    Returns information about all supported export formats including:
    - Format name and description
    - File extension
    - Compression support
    - Human readability

    **Supported Formats:**
    - **JSON**: JavaScript Object Notation - structured, machine-readable
    - **YAML**: YAML Ain't Markup Language - human-friendly, structured
    - **Markdown**: Markdown format - highly readable, documentation-friendly
    """
    return ListFormatsResponse()

