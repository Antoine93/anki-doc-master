"""
Schémas Pydantic pour le Générateur de cartes.

DTOs pour la validation et la sérialisation des requêtes/réponses
HTTP liées à la génération de cartes Anki.
"""
from pydantic import BaseModel, Field, field_validator, ConfigDict
from typing import Literal


class GenerateCardsRequest(BaseModel):
    """DTO pour la requête de génération de cartes."""
    restructuration_id: str = Field(
        ...,
        description="Identifiant de la restructuration source"
    )
    card_type: Literal["basic", "cloze"] = Field(
        default="basic",
        description="Type de carte à générer"
    )
    modules: list[str] | None = Field(
        default=None,
        description="Modules à traiter. Si None, tous sauf images_list et images_descriptions"
    )
    force: bool = Field(
        default=False,
        description="Forcer la re-génération si elle existe déjà"
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "restructuration_id": "abc123def456",
                "card_type": "basic",
                "modules": ["themes", "vocabulary"],
                "force": False
            }
        }
    )


class GenerationResponse(BaseModel):
    """DTO pour la réponse de génération."""
    id: str = Field(..., description="Identifiant de la génération")
    restructuration_id: str = Field(..., description="Identifiant de la restructuration source")
    document_id: str = Field(..., description="Chemin relatif du document")
    document_name: str = Field(..., description="Nom du document")
    card_type: str = Field(..., description="Type de carte généré")
    modules_processed: list[str] = Field(..., description="Modules traités")
    cards_count: dict[str, int] = Field(..., description="Nombre de cartes par module")
    total_cards: int = Field(..., description="Nombre total de cartes")
    output_path: str = Field(..., description="Chemin du dossier output")
    generated_at: str = Field(..., description="Date de génération")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "id": "gen123abc456",
                "restructuration_id": "abc123def456",
                "document_id": "biologie/cellule",
                "document_name": "cellule",
                "card_type": "basic",
                "modules_processed": ["themes", "vocabulary"],
                "cards_count": {"themes": 15, "vocabulary": 42},
                "total_cards": 57,
                "output_path": "outputs/biologie/cellule/analysis-id/cards/basic",
                "generated_at": "2025-01-26T14:30:00"
            }
        }
    )


class GenerationListResponse(BaseModel):
    """DTO pour la liste des générations."""
    generations: list[GenerationResponse] = Field(...)
    total: int = Field(...)


class BasicCardResponse(BaseModel):
    """DTO pour une carte basic (question/réponse)."""
    id: str = Field(..., description="Identifiant de la carte")
    module: str = Field(..., description="Module source")
    card_type: str = Field(..., description="Type de carte")
    front: str = Field(..., description="Question (recto)")
    back: str = Field(..., description="Réponse (verso)")
    tags: list[str] = Field(default=[], description="Tags de la carte")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "id": "card-1",
                "module": "themes",
                "card_type": "basic",
                "front": "Qu'est-ce qu'une machine de Moore ?",
                "back": "Une machine à états finis dont la sortie dépend uniquement de l'état courant.",
                "tags": ["FSM", "Moore"]
            }
        }
    )


class ClozeCardResponse(BaseModel):
    """DTO pour une carte cloze (texte à trous)."""
    id: str = Field(..., description="Identifiant de la carte")
    module: str = Field(..., description="Module source")
    card_type: str = Field(..., description="Type de carte")
    text: str = Field(..., description="Texte avec syntaxe cloze {{c1::...}}")
    tags: list[str] = Field(default=[], description="Tags de la carte")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "id": "card-1",
                "module": "themes",
                "card_type": "cloze",
                "text": "Une {{c1::machine de Moore}} est une FSM dont la sortie dépend uniquement de {{c2::l'état courant}}.",
                "tags": ["FSM", "Moore"]
            }
        }
    )


class CardsListResponse(BaseModel):
    """DTO pour la liste des cartes."""
    cards: list[dict] = Field(..., description="Liste des cartes")
    total: int = Field(..., description="Nombre total de cartes")
    card_type: str = Field(..., description="Type de carte")
    module: str | None = Field(None, description="Module filtré (si applicable)")
