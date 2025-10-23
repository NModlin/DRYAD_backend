"""
Pydantic schemas for project proposal generation.
"""

from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List, Dict, Any
from datetime import datetime


class ProposalGenerateRequest(BaseModel):
    """Request schema for generating a project proposal."""
    
    proposal_type: str = Field(
        default="general",
        description="Type of proposal: general, technical, business, research"
    )
    focus_areas: Optional[List[str]] = Field(
        default=None,
        description="Specific areas to focus on in the analysis"
    )
    additional_context: Optional[str] = Field(
        default=None,
        description="Additional context or requirements for the proposal"
    )
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "proposal_type": "business",
                "focus_areas": ["market analysis", "competitive landscape", "financial projections"],
                "additional_context": "Focus on B2B SaaS market opportunities"
            }
        }
    )


class ProposalMetadata(BaseModel):
    """Metadata about the generated proposal."""
    
    documents_analyzed: int = Field(description="Number of documents analyzed")
    total_documents: int = Field(description="Total documents available")
    proposal_type: str = Field(description="Type of proposal generated")
    generated_at: str = Field(description="ISO timestamp of generation")
    model_used: str = Field(description="AI model used for generation")


class ProposalContent(BaseModel):
    """Content of the generated proposal."""
    
    full_text: str = Field(description="Complete proposal text in markdown format")
    sections: Dict[str, str] = Field(description="Proposal broken down by sections")
    word_count: int = Field(description="Total word count")
    char_count: int = Field(description="Total character count")


class ProposalGenerateResponse(BaseModel):
    """Response schema for proposal generation."""
    
    success: bool = Field(description="Whether proposal generation was successful")
    proposal: Optional[ProposalContent] = Field(
        default=None,
        description="Generated proposal content"
    )
    metadata: Optional[ProposalMetadata] = Field(
        default=None,
        description="Metadata about the proposal generation"
    )
    error: Optional[str] = Field(
        default=None,
        description="Error message if generation failed"
    )
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "success": True,
                "proposal": {
                    "full_text": "# Executive Summary\n\nThis project aims to...",
                    "sections": {
                        "executive_summary": "This project aims to...",
                        "project_overview": "The project scope includes..."
                    },
                    "word_count": 2500,
                    "char_count": 15000
                },
                "metadata": {
                    "documents_analyzed": 15,
                    "total_documents": 15,
                    "proposal_type": "business",
                    "generated_at": "2024-01-15T10:30:00Z",
                    "model_used": "gemini-1.5-pro"
                }
            }
        }
    )


class ProposalStatusResponse(BaseModel):
    """Response schema for checking proposal service status."""
    
    available: bool = Field(description="Whether proposal service is available")
    model: Optional[str] = Field(default=None, description="AI model being used")
    error: Optional[str] = Field(default=None, description="Error message if unavailable")
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "available": True,
                "model": "gemini-1.5-pro"
            }
        }
    )

