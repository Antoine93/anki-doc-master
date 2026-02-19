"""
Schémas Pydantic pour le Formatter (Export Anki).

DTOs pour la validation et la sérialisation des requêtes/réponses
HTTP liées au formatage des cartes en fichiers Anki .txt.
"""
from pydantic import BaseModel, Field, ConfigDict


class FormatCardsRequest(BaseModel):
    """DTO pour la requête de formatage de cartes."""
    optimization_id: str = Field(
        ...,
        description="Identifiant de l'optimisation source"
    )
    force: bool = Field(
        default=False,
        description="Forcer le re-formatage si déjà existant"
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "optimization_id": "opt123abc456",
                "force": False
            }
        }
    )


class FormattingResponse(BaseModel):
    """DTO pour la réponse de formatage."""
    id: str = Field(..., description="Identifiant du formatage")
    optimization_id: str = Field(
        ...,
        description="Identifiant de l'optimisation source"
    )
    document_id: str = Field(..., description="Chemin relatif du document")
    document_name: str = Field(..., description="Nom du document")
    card_type: str = Field(..., description="Type de carte formaté")
    cards_count: int = Field(..., description="Nombre de cartes formatées")
    output_file: str = Field(..., description="Chemin du fichier .txt généré")
    formatted_at: str = Field(..., description="Date de formatage")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "id": "fmt123abc456",
                "optimization_id": "opt123abc456",
                "document_id": "biologie/cellule",
                "document_name": "cellule",
                "card_type": "basic",
                "cards_count": 68,
                "output_file": "outputs/biologie/cellule/analysis-id/cards/anki/basic.txt",
                "formatted_at": "2025-01-26T16:00:00"
            }
        }
    )


class FormattingListResponse(BaseModel):
    """DTO pour la liste des formatages."""
    formattings: list[FormattingResponse] = Field(...)
    total: int = Field(...)


class FormattedContentResponse(BaseModel):
    """DTO pour le contenu du fichier Anki."""
    formatting_id: str = Field(..., description="Identifiant du formatage")
    card_type: str = Field(..., description="Type de carte")
    content: str = Field(..., description="Contenu du fichier Anki .txt")
    lines_count: int = Field(..., description="Nombre de lignes")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "formatting_id": "fmt123abc456",
                "card_type": "basic",
                "content": "#separator:;\n#html:true\nQuestion;Réponse",
                "lines_count": 3
            }
        }
    )
