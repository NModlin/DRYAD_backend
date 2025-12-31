from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, ConfigDict, Field

# --- Vessel ---
class VesselBase(BaseModel):
    storage_path: Optional[str] = None
    file_manifest: Dict[str, Any] = Field(default_factory=dict)

class VesselResponse(VesselBase):
    id: str
    branch_id: str
    created_at: datetime
    updated_at: datetime
    model_config = ConfigDict(from_attributes=True)

# --- Branch ---
class BranchBase(BaseModel):
    name: str
    description: Optional[str] = None
    status: str = "active"

class BranchCreate(BranchBase):
    grove_id: str
    parent_id: Optional[str] = None

class BranchUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    status: Optional[str] = None

class BranchResponse(BranchBase):
    id: str
    grove_id: str
    parent_id: Optional[str]
    created_at: datetime
    updated_at: datetime
    vessel: Optional[VesselResponse] = None
    model_config = ConfigDict(from_attributes=True)

# --- Grove ---
class GroveBase(BaseModel):
    name: str
    description: Optional[str] = None
    is_favorite: bool = False

class GroveCreate(GroveBase):
    pass

class GroveUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    is_favorite: Optional[bool] = None

class GroveResponse(GroveBase):
    id: str
    created_at: datetime
    updated_at: datetime
    model_config = ConfigDict(from_attributes=True)
