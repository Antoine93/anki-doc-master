"""
Schémas Pydantic pour les documents.

DTOs pour la validation et la sérialisation des requêtes/réponses
HTTP liées aux documents.
"""
from pydantic import BaseModel, Field, ConfigDict


class DocumentResponse(BaseModel):
    """
    DTO pour la réponse d'un document.

    L'ID est un UUID unique attribué à chaque document.
    Le relative_id est le chemin relatif sans extension pour référence lisible.

    Structure outputs: outputs/{id}/{analysis_id}/
    """
    id: str = Field(..., description="UUID unique du document (12 caractères)")
    relative_id: str = Field(..., description="Chemin relatif sans extension (ex: biologie/cellule)")
    name: str = Field(..., description="Nom du fichier sans extension")
    filename: str = Field(..., description="Nom complet du fichier avec extension")
    path: str = Field(..., description="Chemin absolu")
    relative_path: str = Field(..., description="Chemin relatif depuis sources/")
    size_bytes: int = Field(..., description="Taille en octets")
    created_at: str = Field(..., description="Date de création (ISO format)")
    has_analysis: bool = Field(False, description="True si le document a été analysé")

    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "id": "a1b2c3d4e5f6",
                "relative_id": "biologie/cellule",
                "name": "cellule",
                "filename": "cellule.pdf",
                "path": "C:/project/sources/biologie/cellule.pdf",
                "relative_path": "biologie/cellule.pdf",
                "size_bytes": 1024000,
                "created_at": "2025-01-26T10:30:00",
                "has_analysis": True
            }
        }
    )


class DocumentListResponse(BaseModel):
    """DTO pour la liste des documents."""
    documents: list[DocumentResponse] = Field(..., description="Liste des documents")
    total: int = Field(..., description="Nombre total de documents")
