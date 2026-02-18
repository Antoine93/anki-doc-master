"""
Schémas Pydantic pour l'API FastAPI.

Ces DTOs gèrent la validation et la sérialisation des données HTTP.
"""
from src.adapters.primary.fastapi.schemas.document_schemas import (
    DocumentResponse,
    DocumentListResponse
)
from src.adapters.primary.fastapi.schemas.analysis_schemas import (
    AnalysisResponse,
    AnalysisListResponse,
    AnalyzeDocumentRequest,
    ModuleResponse,
    ModuleListResponse
)

__all__ = [
    "DocumentResponse",
    "DocumentListResponse",
    "AnalysisResponse",
    "AnalysisListResponse",
    "AnalyzeDocumentRequest",
    "ModuleResponse",
    "ModuleListResponse",
]
