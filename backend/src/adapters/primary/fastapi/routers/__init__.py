"""
Routers FastAPI.

Expose les endpoints HTTP de l'API.
"""
from src.adapters.primary.fastapi.routers.analyst_router import router as analyst_router

__all__ = [
    "analyst_router",
]
