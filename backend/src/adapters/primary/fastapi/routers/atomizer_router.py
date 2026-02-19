"""
Router FastAPI pour l'Atomizer (Optimiseur SuperMemo).

Expose les endpoints HTTP pour l'optimisation des cartes Anki.
"""
import logging
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status, Query

from src.adapters.primary.fastapi.schemas.atomizer_schemas import (
    OptimizeCardsRequest,
    OptimizationResponse,
    OptimizationListResponse,
    OptimizedCardsListResponse
)
from src.ports.primary.optimize_cards_use_case import OptimizeCardsUseCase


logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/atomizer",
    tags=["Atomizer"]
)


def get_atomizer_use_cases() -> OptimizeCardsUseCase:
    """Injection du service Atomizer."""
    from src.di_container import get_atomizer_service
    return get_atomizer_service()


AtomizerUseCasesDep = Annotated[
    OptimizeCardsUseCase,
    Depends(get_atomizer_use_cases)
]


# ===== ENDPOINTS OPTIMISATION =====

@router.post(
    "/optimizations",
    response_model=OptimizationResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Optimiser des cartes selon SuperMemo",
    description="Optimise les cartes d'une génération existante selon les règles SuperMemo "
                "(atomisation, simplification, anti-interférence)."
)
def optimize_cards(
    request: OptimizeCardsRequest,
    use_cases: AtomizerUseCasesDep
) -> OptimizationResponse:
    """Endpoint POST /api/atomizer/optimizations"""
    try:
        result = use_cases.optimize_cards(
            generation_id=request.generation_id,
            content_types=request.content_types,
            force=request.force
        )
        return OptimizationResponse(**result)

    except Exception as e:
        error_type = type(e).__name__

        if error_type == "GenerationNotFoundError":
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
        elif error_type == "OptimizationAlreadyExistsError":
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))
        elif error_type == "DomainValidationError":
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
        elif error_type == "AIError":
            logger.error(f"Erreur IA: {e}", exc_info=True)
            raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(e))

        logger.error(f"Erreur optimisation: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erreur interne"
        )


@router.get(
    "/optimizations",
    response_model=OptimizationListResponse,
    summary="Lister les optimisations",
    description="Liste toutes les optimisations de cartes existantes"
)
def list_optimizations(
    use_cases: AtomizerUseCasesDep,
    document_id: str | None = Query(None, description="Filtrer par document")
) -> OptimizationListResponse:
    """Endpoint GET /api/atomizer/optimizations"""
    try:
        optimizations = use_cases.list_optimizations(document_id)
        return OptimizationListResponse(
            optimizations=[OptimizationResponse(**o) for o in optimizations],
            total=len(optimizations)
        )
    except Exception as e:
        logger.error(f"Erreur listing: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erreur interne"
        )


@router.get(
    "/optimizations/{optimization_id}",
    response_model=OptimizationResponse,
    summary="Récupérer une optimisation",
    description="Récupère les détails d'une optimisation de cartes"
)
def get_optimization(
    optimization_id: str,
    use_cases: AtomizerUseCasesDep
) -> OptimizationResponse:
    """Endpoint GET /api/atomizer/optimizations/{id}"""
    try:
        result = use_cases.get_optimization(optimization_id)
        return OptimizationResponse(**result)
    except Exception as e:
        if type(e).__name__ == "OptimizationNotFoundError":
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
        logger.error(f"Erreur: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erreur interne"
        )


@router.get(
    "/generations/{generation_id}/optimization",
    response_model=OptimizationResponse,
    summary="Récupérer l'optimisation d'une génération",
    description="Récupère l'optimisation associée à une génération de cartes"
)
def get_generation_optimization(
    generation_id: str,
    use_cases: AtomizerUseCasesDep
) -> OptimizationResponse:
    """Endpoint GET /api/atomizer/generations/{id}/optimization"""
    try:
        result = use_cases.get_optimization_by_generation(generation_id)
        if result is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Aucune optimisation pour la génération {generation_id}"
            )
        return OptimizationResponse(**result)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erreur: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erreur interne"
        )


@router.delete(
    "/optimizations/{optimization_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Supprimer une optimisation",
    description="Supprime une optimisation et ses cartes"
)
def delete_optimization(
    optimization_id: str,
    use_cases: AtomizerUseCasesDep
) -> None:
    """Endpoint DELETE /api/atomizer/optimizations/{id}"""
    try:
        use_cases.delete_optimization(optimization_id)
    except Exception as e:
        if type(e).__name__ == "OptimizationNotFoundError":
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
        logger.error(f"Erreur: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erreur interne"
        )


# ===== ENDPOINTS CARTES OPTIMISÉES =====

@router.get(
    "/optimizations/{optimization_id}/cards",
    response_model=OptimizedCardsListResponse,
    summary="Récupérer les cartes optimisées",
    description="Récupère toutes les cartes optimisées, avec filtrage optionnel par module"
)
def get_optimized_cards(
    optimization_id: str,
    use_cases: AtomizerUseCasesDep,
    module: str | None = Query(None, description="Filtrer par module")
) -> OptimizedCardsListResponse:
    """Endpoint GET /api/atomizer/optimizations/{id}/cards"""
    try:
        optimization = use_cases.get_optimization(optimization_id)
        cards = use_cases.get_optimized_cards(optimization_id, module)

        return OptimizedCardsListResponse(
            cards=cards,
            total=len(cards),
            card_type=optimization["card_type"],
            module=module
        )
    except Exception as e:
        error_type = type(e).__name__
        if error_type == "OptimizationNotFoundError":
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
        logger.error(f"Erreur: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erreur interne"
        )


@router.get(
    "/optimizations/{optimization_id}/cards/{card_id}",
    summary="Récupérer une carte optimisée spécifique",
    description="Récupère une carte optimisée par son identifiant"
)
def get_optimized_card(
    optimization_id: str,
    card_id: str,
    use_cases: AtomizerUseCasesDep
) -> dict:
    """Endpoint GET /api/atomizer/optimizations/{id}/cards/{card_id}"""
    try:
        return use_cases.get_optimized_card(optimization_id, card_id)
    except Exception as e:
        error_type = type(e).__name__
        if error_type in ["OptimizationNotFoundError", "CardNotFoundError"]:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
        logger.error(f"Erreur: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erreur interne"
        )
