"""
Router FastAPI pour le Générateur de cartes.

Expose les endpoints HTTP pour la génération de cartes Anki.
"""
import logging
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status, Query

from src.adapters.primary.fastapi.schemas.generator_schemas import (
    GenerateCardsRequest,
    GenerationResponse,
    GenerationListResponse,
    CardsListResponse
)
from src.ports.primary.generate_cards_use_case import GenerateCardsUseCase


logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/generator",
    tags=["Generator"]
)


def get_generator_use_cases() -> GenerateCardsUseCase:
    """Injection du service Générateur."""
    from src.di_container import get_generator_service
    return get_generator_service()


GeneratorUseCasesDep = Annotated[
    GenerateCardsUseCase,
    Depends(get_generator_use_cases)
]


# ===== ENDPOINTS GÉNÉRATION =====

@router.post(
    "/generations",
    response_model=GenerationResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Générer des cartes Anki",
    description="Génère des cartes Anki à partir d'une restructuration existante. "
                "Supporte les types 'basic' (question/réponse) et 'cloze' (texte à trous)."
)
def generate_cards(
    request: GenerateCardsRequest,
    use_cases: GeneratorUseCasesDep
) -> GenerationResponse:
    """Endpoint POST /api/generator/generations"""
    try:
        result = use_cases.generate_cards(
            restructuration_id=request.restructuration_id,
            card_type=request.card_type,
            modules=request.modules,
            force=request.force
        )
        return GenerationResponse(**result)

    except Exception as e:
        error_type = type(e).__name__

        if error_type == "RestructurationNotFoundError":
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
        elif error_type == "GenerationAlreadyExistsError":
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))
        elif error_type == "DomainValidationError":
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
        elif error_type == "AIError":
            logger.error(f"Erreur IA: {e}", exc_info=True)
            raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(e))

        logger.error(f"Erreur génération: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erreur interne"
        )


@router.get(
    "/generations",
    response_model=GenerationListResponse,
    summary="Lister les générations",
    description="Liste toutes les générations de cartes existantes"
)
def list_generations(
    use_cases: GeneratorUseCasesDep,
    document_id: str | None = Query(None, description="Filtrer par document")
) -> GenerationListResponse:
    """Endpoint GET /api/generator/generations"""
    try:
        generations = use_cases.list_generations(document_id)
        return GenerationListResponse(
            generations=[GenerationResponse(**g) for g in generations],
            total=len(generations)
        )
    except Exception as e:
        logger.error(f"Erreur listing: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erreur interne"
        )


@router.get(
    "/generations/{generation_id}",
    response_model=GenerationResponse,
    summary="Récupérer une génération",
    description="Récupère les détails d'une génération de cartes"
)
def get_generation(
    generation_id: str,
    use_cases: GeneratorUseCasesDep
) -> GenerationResponse:
    """Endpoint GET /api/generator/generations/{id}"""
    try:
        result = use_cases.get_generation(generation_id)
        return GenerationResponse(**result)
    except Exception as e:
        if type(e).__name__ == "GenerationNotFoundError":
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
        logger.error(f"Erreur: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erreur interne"
        )


@router.get(
    "/restructurations/{restructuration_id}/generation",
    response_model=GenerationResponse,
    summary="Récupérer la génération d'une restructuration",
    description="Récupère la génération de cartes associée à une restructuration"
)
def get_restructuration_generation(
    restructuration_id: str,
    use_cases: GeneratorUseCasesDep,
    card_type: str | None = Query(None, description="Filtrer par type de carte")
) -> GenerationResponse:
    """Endpoint GET /api/generator/restructurations/{id}/generation"""
    try:
        result = use_cases.get_generation_by_restructuration(restructuration_id, card_type)
        if result is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Aucune génération pour la restructuration {restructuration_id}"
            )
        return GenerationResponse(**result)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erreur: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erreur interne"
        )


@router.delete(
    "/generations/{generation_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Supprimer une génération",
    description="Supprime une génération et ses cartes"
)
def delete_generation(
    generation_id: str,
    use_cases: GeneratorUseCasesDep
) -> None:
    """Endpoint DELETE /api/generator/generations/{id}"""
    try:
        use_cases.delete_generation(generation_id)
    except Exception as e:
        if type(e).__name__ == "GenerationNotFoundError":
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
        logger.error(f"Erreur: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erreur interne"
        )


# ===== ENDPOINTS CARTES =====

@router.get(
    "/generations/{generation_id}/cards",
    response_model=CardsListResponse,
    summary="Récupérer les cartes d'une génération",
    description="Récupère toutes les cartes générées, avec filtrage optionnel par module"
)
def get_cards(
    generation_id: str,
    use_cases: GeneratorUseCasesDep,
    module: str | None = Query(None, description="Filtrer par module")
) -> CardsListResponse:
    """Endpoint GET /api/generator/generations/{id}/cards"""
    try:
        # Récupérer les infos de la génération pour le card_type
        generation = use_cases.get_generation(generation_id)
        cards = use_cases.get_cards(generation_id, module)

        return CardsListResponse(
            cards=cards,
            total=len(cards),
            card_type=generation["card_type"],
            module=module
        )
    except Exception as e:
        error_type = type(e).__name__
        if error_type == "GenerationNotFoundError":
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
        logger.error(f"Erreur: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erreur interne"
        )


@router.get(
    "/generations/{generation_id}/cards/{card_id}",
    summary="Récupérer une carte spécifique",
    description="Récupère une carte par son identifiant"
)
def get_card(
    generation_id: str,
    card_id: str,
    use_cases: GeneratorUseCasesDep
) -> dict:
    """Endpoint GET /api/generator/generations/{id}/cards/{card_id}"""
    try:
        return use_cases.get_card(generation_id, card_id)
    except Exception as e:
        error_type = type(e).__name__
        if error_type in ["GenerationNotFoundError", "CardNotFoundError"]:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
        logger.error(f"Erreur: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erreur interne"
        )
