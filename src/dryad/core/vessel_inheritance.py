from dryad.database.models.vessel import Vessel

class VesselInheritanceManager:
    async def resolve_full_inherited_context(self, vessel: Vessel, db: Any) -> str:
        return ""
