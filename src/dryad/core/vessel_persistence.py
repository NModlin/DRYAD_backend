from dryad.database.models.vessel import Vessel

class VesselPersistenceService:
    async def load_vessel_content(self, vessel: Vessel):
        # Return a dummy content object or dict
        return DummyContent()

    async def save_vessel_content(self, vessel: Vessel, content: Any):
        pass

class DummyContent:
    metadata = {}
    summary = ""
    base_context = ""
    branch_context = ""
    dialogues = []
