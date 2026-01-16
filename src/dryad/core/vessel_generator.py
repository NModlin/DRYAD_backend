from typing import Optional, Dict, Any
from pydantic import BaseModel
from dryad.database.models.vessel import Vessel
import uuid

class VesselCreationOptions(BaseModel):
    parent_branch_id: Optional[str] = None
    initial_content: Optional[Dict[str, Any]] = None

class VesselGenerator:
    """
    Generator for creating new vessels.
    """
    async def create_vessel(self, branch_id: str, options: VesselCreationOptions) -> Vessel:
        """
        Create a new vessel for a branch.
        """
        vessel = Vessel(
            id=str(uuid.uuid4()),
            branch_id=branch_id,
            status="active",
            # Add other default fields as necessary based on Vessel model
        )
        return vessel
