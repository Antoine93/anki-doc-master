"""
Schémas Pydantic pour les analyses.

DTOs pour la validation et la sérialisation des requêtes/réponses
HTTP liées aux analyses de documents.
"""
from pydantic import BaseModel, Field, ConfigDict


class AnalysisResponse(BaseModel):
    """
    DTO pour la réponse d'une analyse.

    Format fixe et minimaliste - liste des modules détectés.
    L'analysis_id est l'identifiant unique de l'analyse et sert aussi de nom de dossier.
    """
    analysis_id: str = Field(..., description="Identifiant unique de l'analyse (sert aussi de nom de dossier)")
    document_id: str = Field(..., description="Chemin relatif du document (ex: biologie/cellule)")
    detected_modules: list[str] = Field(..., description="Modules détectés")
    output_path: str = Field(..., description="Chemin du dossier output")
    analyzed_at: str = Field(..., description="Date de l'analyse (ISO format)")

    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "analysis_id": "a2c95734f24b",
                "document_id": "biologie/cellule",
                "detected_modules": ["themes", "vocabulary", "images_list", "tables"],
                "output_path": "outputs/biologie/cellule/a2c95734f24b",
                "analyzed_at": "2025-01-26T10:30:00"
            }
        }
    )


class AnalysisListResponse(BaseModel):
    """DTO pour la liste des analyses."""
    analyses: list[AnalysisResponse] = Field(...)
    total: int = Field(...)


class AnalyzeDocumentRequest(BaseModel):
    """DTO pour la requête d'analyse."""
    document_id: str = Field(..., description="Chemin relatif du document (ex: biologie/cellule)")
    force: bool = Field(default=False, description="Forcer la ré-analyse si elle existe déjà")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "document_id": "biologie/cellule",
                "force": False
            }
        }
    )


class ModuleResponse(BaseModel):
    """DTO pour un module disponible."""
    id: str = Field(..., description="Identifiant du module")
    description: str = Field(..., description="Description du module")


class ModuleListResponse(BaseModel):
    """DTO pour la liste des modules."""
    modules: list[ModuleResponse] = Field(...)
