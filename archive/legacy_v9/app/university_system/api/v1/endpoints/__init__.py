"""
API endpoints package for Uni0
"""

# Import endpoints for easy access
from . import universities
from . import curriculum
from . import competitions
from . import enhanced_university
from . import health
from . import websocket
from . import auth

__all__ = [
    "universities",
    "curriculum", 
    "competitions",
    "enhanced_university",
    "health",
    "websocket",
    "auth"
]