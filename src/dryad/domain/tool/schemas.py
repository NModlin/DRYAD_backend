from datetime import datetime
from typing import Optional, Any, Dict
from pydantic import BaseModel, ConfigDict, Field

class ToolBase(BaseModel):
    name: str = Field(..., description="Unique name of the tool")
    description: Optional[str] = None
    version: str = "1.0.0"
    category: str = "general"
    security_level: str = "standard"
    is_active: bool = True
    requires_sandbox: bool = False
    sandbox_image: Optional[str] = None
    input_schema: Dict[str, Any] = Field(default_factory=dict, description="JSON Schema for input parameters")

class ToolCreate(ToolBase):
    pass

class ToolUpdate(BaseModel):
    description: Optional[str] = None
    version: Optional[str] = None
    is_active: Optional[bool] = None
    input_schema: Optional[Dict[str, Any]] = None

class ToolResponse(ToolBase):
    id: str
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
