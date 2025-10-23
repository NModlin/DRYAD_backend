"""
Export/Import Schemas for Dryad

Pydantic schemas for exporting and importing Dryad knowledge structures.
"""

from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field


# ============================================================================
# Enums
# ============================================================================

class ExportFormat(str, Enum):
    """Supported export formats."""
    JSON = "json"
    YAML = "yaml"
    MARKDOWN = "markdown"


class ImportStrategy(str, Enum):
    """Import merge strategies."""
    CREATE_NEW = "create_new"  # Create new grove with new IDs
    MERGE_EXISTING = "merge_existing"  # Merge into existing grove
    SKIP_DUPLICATES = "skip_duplicates"  # Skip items that already exist
    OVERWRITE = "overwrite"  # Overwrite existing items


class ExportScope(str, Enum):
    """Scope of export."""
    FULL = "full"  # Export everything
    BRANCHES_ONLY = "branches_only"  # Export branches without vessels/dialogues
    METADATA_ONLY = "metadata_only"  # Export only metadata, no content


# ============================================================================
# Export Request/Response Schemas
# ============================================================================

class ExportFilters(BaseModel):
    """Filters for selective export."""
    branch_ids: Optional[List[str]] = Field(default=None, description="Specific branch IDs to export")
    include_archived: bool = Field(default=False, description="Include archived branches")
    min_priority: Optional[str] = Field(default=None, description="Minimum branch priority")
    created_after: Optional[datetime] = Field(default=None, description="Only export items created after this date")
    created_before: Optional[datetime] = Field(default=None, description="Only export items created before this date")
    max_depth: Optional[int] = Field(default=None, description="Maximum branch depth to export")


class ExportOptions(BaseModel):
    """Options for export operation."""
    format: ExportFormat = Field(default=ExportFormat.JSON, description="Export format")
    scope: ExportScope = Field(default=ExportScope.FULL, description="Scope of export")
    filters: Optional[ExportFilters] = Field(default=None, description="Filters for selective export")
    include_vessel_content: bool = Field(default=True, description="Include vessel file content")
    include_dialogue_messages: bool = Field(default=True, description="Include dialogue messages")
    include_suggestions: bool = Field(default=True, description="Include branch suggestions")
    include_observation_points: bool = Field(default=True, description="Include observation points")
    compress: bool = Field(default=False, description="Compress export file")
    pretty_print: bool = Field(default=True, description="Pretty print JSON/YAML")


class ExportRequest(BaseModel):
    """Request to export a grove."""
    grove_id: str = Field(..., description="Grove ID to export")
    options: ExportOptions = Field(default_factory=ExportOptions, description="Export options")


class ExportMetadata(BaseModel):
    """Metadata about the export."""
    export_version: str = Field(default="1.0.0", description="Export format version")
    exported_at: datetime = Field(default_factory=datetime.utcnow, description="Export timestamp")
    grove_id: str = Field(..., description="Original grove ID")
    grove_name: str = Field(..., description="Grove name")
    total_branches: int = Field(..., description="Total branches exported")
    total_vessels: int = Field(default=0, description="Total vessels exported")
    total_dialogues: int = Field(default=0, description="Total dialogues exported")
    total_suggestions: int = Field(default=0, description="Total suggestions exported")
    export_options: ExportOptions = Field(..., description="Export options used")


class ExportResponse(BaseModel):
    """Response from export operation."""
    success: bool = Field(..., description="Whether export succeeded")
    metadata: ExportMetadata = Field(..., description="Export metadata")
    data: Optional[Dict[str, Any]] = Field(default=None, description="Exported data (if not file)")
    file_path: Optional[str] = Field(default=None, description="Path to exported file")
    file_size_bytes: Optional[int] = Field(default=None, description="Size of exported file")
    export_time_ms: float = Field(..., description="Time taken to export (milliseconds)")
    warnings: List[str] = Field(default_factory=list, description="Warnings during export")


# ============================================================================
# Import Request/Response Schemas
# ============================================================================

class ImportValidationResult(BaseModel):
    """Result of import validation."""
    is_valid: bool = Field(..., description="Whether import data is valid")
    errors: List[str] = Field(default_factory=list, description="Validation errors")
    warnings: List[str] = Field(default_factory=list, description="Validation warnings")
    compatible_version: bool = Field(..., description="Whether export version is compatible")
    total_items: int = Field(..., description="Total items to import")


class ImportOptions(BaseModel):
    """Options for import operation."""
    strategy: ImportStrategy = Field(default=ImportStrategy.CREATE_NEW, description="Import strategy")
    target_grove_id: Optional[str] = Field(default=None, description="Target grove ID (for merge)")
    validate_only: bool = Field(default=False, description="Only validate, don't import")
    skip_validation: bool = Field(default=False, description="Skip validation (dangerous)")
    preserve_ids: bool = Field(default=False, description="Preserve original IDs")
    preserve_timestamps: bool = Field(default=False, description="Preserve original timestamps")
    import_vessel_content: bool = Field(default=True, description="Import vessel file content")
    import_dialogue_messages: bool = Field(default=True, description="Import dialogue messages")
    import_suggestions: bool = Field(default=True, description="Import branch suggestions")
    import_observation_points: bool = Field(default=True, description="Import observation points")


class ImportRequest(BaseModel):
    """Request to import a grove."""
    data: Optional[Dict[str, Any]] = Field(default=None, description="Import data (inline)")
    file_path: Optional[str] = Field(default=None, description="Path to import file")
    format: ExportFormat = Field(default=ExportFormat.JSON, description="Import format")
    options: ImportOptions = Field(default_factory=ImportOptions, description="Import options")


class ImportStats(BaseModel):
    """Statistics from import operation."""
    groves_created: int = Field(default=0, description="Groves created")
    groves_updated: int = Field(default=0, description="Groves updated")
    branches_created: int = Field(default=0, description="Branches created")
    branches_updated: int = Field(default=0, description="Branches updated")
    branches_skipped: int = Field(default=0, description="Branches skipped")
    vessels_created: int = Field(default=0, description="Vessels created")
    dialogues_created: int = Field(default=0, description="Dialogues created")
    suggestions_created: int = Field(default=0, description="Suggestions created")
    observation_points_created: int = Field(default=0, description="Observation points created")
    errors: int = Field(default=0, description="Errors encountered")


class ImportResponse(BaseModel):
    """Response from import operation."""
    success: bool = Field(..., description="Whether import succeeded")
    validation: Optional[ImportValidationResult] = Field(default=None, description="Validation result")
    stats: ImportStats = Field(default_factory=ImportStats, description="Import statistics")
    grove_id: Optional[str] = Field(default=None, description="Imported/updated grove ID")
    import_time_ms: float = Field(..., description="Time taken to import (milliseconds)")
    errors: List[str] = Field(default_factory=list, description="Errors during import")
    warnings: List[str] = Field(default_factory=list, description="Warnings during import")


# ============================================================================
# Export Data Structures
# ============================================================================

class ExportedBranchSuggestion(BaseModel):
    """Exported branch suggestion."""
    id: str
    dialogue_id: str
    branch_id: str
    created_branch_id: Optional[str]
    suggestion_type: str
    title: str
    description: str
    source_text: str
    priority_score: float
    priority_level: str
    relevance_score: float
    confidence: float
    estimated_depth: int
    keywords: Optional[List[str]]
    metadata: Optional[Dict[str, Any]]
    is_auto_created: bool
    created_at: Optional[datetime]


class ExportedDialogueMessage(BaseModel):
    """Exported dialogue message."""
    id: str
    dialogue_id: str
    role: str
    content: str
    created_at: Optional[datetime]


class ExportedDialogue(BaseModel):
    """Exported dialogue."""
    id: str
    branch_id: str
    oracle_used: str
    insights: Optional[Dict[str, List[str]]]
    storage_path: Optional[str]
    created_at: Optional[datetime]
    messages: List[ExportedDialogueMessage] = Field(default_factory=list)
    suggestions: List[ExportedBranchSuggestion] = Field(default_factory=list)


class ExportedVessel(BaseModel):
    """Exported vessel."""
    id: str
    branch_id: str
    file_references: Dict[str, str]
    content_hash: str
    storage_path: str
    is_compressed: bool
    compressed_path: Optional[str]
    status: str
    created_at: Optional[datetime]
    content: Optional[Dict[str, Any]] = Field(default=None, description="Vessel file content")


class ExportedPossibility(BaseModel):
    """Exported possibility."""
    id: str
    observation_point_id: str
    description: str
    probability: float
    is_manifested: bool
    created_at: Optional[datetime]


class ExportedObservationPoint(BaseModel):
    """Exported observation point."""
    id: str
    branch_id: str
    name: str
    description: Optional[str]
    context: Optional[str]
    created_at: Optional[datetime]
    possibilities: List[ExportedPossibility] = Field(default_factory=list)


class ExportedBranch(BaseModel):
    """Exported branch."""
    id: str
    grove_id: str
    parent_id: Optional[str]
    observation_point_id: Optional[str]
    name: str
    description: Optional[str]
    status: str
    priority: str
    path_depth: int
    created_at: Optional[datetime]
    updated_at: Optional[datetime]
    vessel: Optional[ExportedVessel] = None
    dialogues: List[ExportedDialogue] = Field(default_factory=list)
    observation_points: List[ExportedObservationPoint] = Field(default_factory=list)
    children: List["ExportedBranch"] = Field(default_factory=list, description="Child branches")


class ExportedGrove(BaseModel):
    """Exported grove with full tree structure."""
    id: str
    name: str
    description: Optional[str]
    created_at: Optional[datetime]
    updated_at: Optional[datetime]
    last_accessed_at: Optional[datetime]
    is_favorite: bool
    template_metadata: Optional[Dict[str, Any]]
    branches: List[ExportedBranch] = Field(default_factory=list, description="Root branches")


# ============================================================================
# Format Info
# ============================================================================

class ExportFormatInfo(BaseModel):
    """Information about an export format."""
    format: ExportFormat
    name: str
    description: str
    file_extension: str
    supports_compression: bool
    human_readable: bool


class ListFormatsResponse(BaseModel):
    """Response listing available export formats."""
    formats: List[ExportFormatInfo] = Field(
        default_factory=lambda: [
            ExportFormatInfo(
                format=ExportFormat.JSON,
                name="JSON",
                description="JavaScript Object Notation - structured, machine-readable",
                file_extension=".json",
                supports_compression=True,
                human_readable=True
            ),
            ExportFormatInfo(
                format=ExportFormat.YAML,
                name="YAML",
                description="YAML Ain't Markup Language - human-friendly, structured",
                file_extension=".yaml",
                supports_compression=True,
                human_readable=True
            ),
            ExportFormatInfo(
                format=ExportFormat.MARKDOWN,
                name="Markdown",
                description="Markdown format - highly readable, documentation-friendly",
                file_extension=".md",
                supports_compression=True,
                human_readable=True
            )
        ]
    )

