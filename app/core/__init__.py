# app/core/__init__.py
"""
Core module for DRYAD.AI Backend.
Exposes main components for easy importing.
"""

# Import core modules with optional heavy deps protected
from . import orchestrator
from . import security
from . import exceptions

# Optional imports (guarded to avoid bringing heavy deps during smoke tests)
try:
    from . import agent_system  # may import multi_agent transitively
except Exception:
    agent_system = None
try:
    from . import agent
except Exception:
    agent = None
try:
    from . import multi_agent
except Exception:
    multi_agent = None

__all__ = [
    name for name, val in [
        ("orchestrator", orchestrator),
        ("security", security),
        ("exceptions", exceptions),
        ("agent_system", agent_system),
        ("agent", agent),
        ("multi_agent", multi_agent),
    ] if val is not None
]
