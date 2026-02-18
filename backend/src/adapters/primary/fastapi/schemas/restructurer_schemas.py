"""
Schémas Pydantic pour le Restructurateur.

DTOs pour la validation et la sérialisation des requêtes/réponses
HTTP liées à la restructuration de documents.
"""
from pydantic import BaseModel, Field, ConfigDict


class RestructureDocumentRequest(BaseModel):
    """DTO pour la requête de restructuration basée sur une analyse."""
    analysis_id: str = Field(..., description="Identifiant de l'analyse à restructurer")
    force: bool = Field(default=False, description="Forcer la re-restructuration si elle existe déjà")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "analysis_id": "b3ba2e89-604",
                "force": False
            }
        }
    )


class RestructurationResponse(BaseModel):
    """DTO pour la réponse de restructuration."""
    id: str = Field(..., description="Identifiant de la restructuration")
    analysis_id: str = Field(..., description="Identifiant de l'analyse associée")
    document_id: str = Field(..., description="Chemin relatif du document")
    document_name: str = Field(..., description="Nom du document")
    modules_processed: list[str] = Field(..., description="Modules traités")
    items_count: dict[str, int] = Field(..., description="Nombre d'items par module")
    output_path: str = Field(..., description="Chemin du dossier output")
    restructured_at: str = Field(..., description="Date de restructuration")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "id": "abc123def456",
                "analysis_id": "a2c95734f24b",
                "document_id": "biologie/cellule",
                "document_name": "cellule",
                "modules_processed": ["themes", "vocabulary"],
                "items_count": {"themes": 5, "vocabulary": 23},
                "output_path": "outputs/biologie/cellule/a2c95734f24b",
                "restructured_at": "2025-01-26T10:30:00"
            }
        }
    )


class RestructurationListResponse(BaseModel):
    """DTO pour la liste des restructurations."""
    restructurations: list[RestructurationResponse] = Field(...)
    total: int = Field(...)


class ModuleContentResponse(BaseModel):
    """DTO pour le contenu d'un module."""
    module: str = Field(..., description="Nom du module")
    items: list[dict] = Field(..., description="Items du module")
    total: int = Field(..., description="Nombre d'items")
