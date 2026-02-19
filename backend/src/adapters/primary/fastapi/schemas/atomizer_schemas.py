"""
Schémas Pydantic pour l'Atomizer (Optimiseur SuperMemo).

DTOs pour la validation et la sérialisation des requêtes/réponses
HTTP liées à l'optimisation des cartes Anki.
"""
from pydantic import BaseModel, Field, ConfigDict
from typing import Literal


class OptimizeCardsRequest(BaseModel):
    """DTO pour la requête d'optimisation de cartes."""
    generation_id: str = Field(
        ...,
        description="Identifiant de la génération source"
    )
    content_types: list[Literal[
        "general", "math_formulas", "code", "tables", "images"
    ]] | None = Field(
        default=None,
        description="Types de contenu à traiter. Si None, détection automatique"
    )
    force: bool = Field(
        default=False,
        description="Forcer la ré-optimisation si elle existe déjà"
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "generation_id": "gen123abc456",
                "content_types": None,
                "force": False
            }
        }
    )


class ModuleStats(BaseModel):
    """DTO pour les statistiques d'un module."""
    input: int = Field(..., description="Nombre de cartes en entrée")
    output: int = Field(..., description="Nombre de cartes en sortie")
    content_type: str = Field(..., description="Type de contenu détecté")


class OptimizationResponse(BaseModel):
    """DTO pour la réponse d'optimisation."""
    id: str = Field(..., description="Identifiant de l'optimisation")
    generation_id: str = Field(..., description="Identifiant de la génération source")
    document_id: str = Field(..., description="Chemin relatif du document")
    document_name: str = Field(..., description="Nom du document")
    card_type: str = Field(..., description="Type de carte optimisé")
    modules_processed: list[str] = Field(..., description="Modules traités")
    modules_stats: dict[str, ModuleStats] = Field(
        ...,
        description="Statistiques par module"
    )
    cards_input: int = Field(..., description="Nombre total de cartes en entrée")
    cards_output: int = Field(..., description="Nombre total de cartes en sortie")
    optimization_ratio: float = Field(
        ...,
        description="Ratio output/input (>1 = atomisation, <1 = fusion)"
    )
    output_path: str = Field(..., description="Chemin du dossier output")
    optimized_at: str = Field(..., description="Date d'optimisation")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "id": "opt123abc456",
                "generation_id": "gen123abc456",
                "document_id": "biologie/cellule",
                "document_name": "cellule",
                "card_type": "basic",
                "modules_processed": ["themes", "vocabulary"],
                "modules_stats": {
                    "themes": {"input": 15, "output": 23, "content_type": "general"},
                    "vocabulary": {"input": 42, "output": 45, "content_type": "general"}
                },
                "cards_input": 57,
                "cards_output": 68,
                "optimization_ratio": 1.19,
                "output_path": "outputs/biologie/cellule/analysis-id/cards/optimized/basic",
                "optimized_at": "2025-01-26T15:30:00"
            }
        }
    )


class OptimizationListResponse(BaseModel):
    """DTO pour la liste des optimisations."""
    optimizations: list[OptimizationResponse] = Field(...)
    total: int = Field(...)


class OptimizedCardsListResponse(BaseModel):
    """DTO pour la liste des cartes optimisées."""
    cards: list[dict] = Field(..., description="Liste des cartes optimisées")
    total: int = Field(..., description="Nombre total de cartes")
    card_type: str = Field(..., description="Type de carte")
    module: str | None = Field(None, description="Module filtré (si applicable)")
