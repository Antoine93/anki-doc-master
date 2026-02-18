"""
Router FastAPI pour le Restructurateur.

Expose les endpoints HTTP pour la restructuration de documents.
"""
import logging
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status

from src.adapters.primary.fastapi.schemas.restructurer_schemas import (
    RestructureDocumentRequest,
    RestructurationResponse,
    RestructurationListResponse,
    ModuleContentResponse
)
from src.ports.primary.restructure_document_use_case import RestructureDocumentUseCase


logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/restructurer",
    tags=["Restructurer"]
)


def get_restructurer_use_cases() -> RestructureDocumentUseCase:
    """Injection du service Restructurateur."""
    from src.di_container import get_restructurer_service
    return get_restructurer_service()


RestructurerUseCasesDep = Annotated[
    RestructureDocumentUseCase,
    Depends(get_restructurer_use_cases)
]


# ===== ENDPOINTS RESTRUCTURATION =====

@router.post(
    "/restructurations",
    response_model=RestructurationResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Restructurer un document depuis une analyse",
    description="Restructure un document PDF à partir d'une analyse existante. "
                "Les modules détectés dans l'analyse sont utilisés automatiquement."
)
def restructure_document(
    request: RestructureDocumentRequest,
    use_cases: RestructurerUseCasesDep
) -> RestructurationResponse:
    """Endpoint POST /api/restructurer/restructurations"""
    try:
        result = use_cases.restructure_document(
            analysis_id=request.analysis_id,
            force=request.force
        )
        return RestructurationResponse(**result)

    except Exception as e:
        error_type = type(e).__name__

        if error_type == "AnalysisNotFoundError":
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
        elif error_type == "DocumentNotFoundError":
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
        elif error_type == "RestructurationAlreadyExistsError":
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))
        elif error_type == "DomainValidationError":
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
        elif error_type == "AIError":
            logger.error(f"Erreur IA: {e}", exc_info=True)
            raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(e))

        logger.error(f"Erreur restructuration: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erreur interne"
        )


@router.get(
    "/restructurations",
    response_model=RestructurationListResponse,
    summary="Lister les restructurations",
    description="Liste toutes les restructurations existantes"
)
def list_restructurations(use_cases: RestructurerUseCasesDep) -> RestructurationListResponse:
    """Endpoint GET /api/restructurer/restructurations"""
    try:
        restructurations = use_cases.list_restructurations()
        return RestructurationListResponse(
            restructurations=[RestructurationResponse(**r) for r in restructurations],
            total=len(restructurations)
        )
    except Exception as e:
        logger.error(f"Erreur listing: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erreur interne"
        )


@router.get(
    "/restructurations/{restructuration_id}",
    response_model=RestructurationResponse,
    summary="Récupérer une restructuration",
    description="Récupère les détails d'une restructuration"
)
def get_restructuration(
    restructuration_id: str,
    use_cases: RestructurerUseCasesDep
) -> RestructurationResponse:
    """Endpoint GET /api/restructurer/restructurations/{id}"""
    try:
        result = use_cases.get_restructuration(restructuration_id)
        return RestructurationResponse(**result)
    except Exception as e:
        if type(e).__name__ == "RestructurationNotFoundError":
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
        logger.error(f"Erreur: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erreur interne"
        )


@router.get(
    "/documents/{document_id}/restructuration",
    response_model=RestructurationResponse,
    summary="Récupérer la restructuration d'un document",
    description="Récupère la restructuration associée à un document"
)
def get_document_restructuration(
    document_id: str,
    use_cases: RestructurerUseCasesDep
) -> RestructurationResponse:
    """Endpoint GET /api/restructurer/documents/{id}/restructuration"""
    try:
        result = use_cases.get_restructuration_by_document(document_id)
        if result is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Aucune restructuration pour {document_id}"
            )
        return RestructurationResponse(**result)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erreur: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erreur interne"
        )


@router.delete(
    "/restructurations/{restructuration_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Supprimer une restructuration",
    description="Supprime une restructuration et ses fichiers"
)
def delete_restructuration(
    restructuration_id: str,
    use_cases: RestructurerUseCasesDep
) -> None:
    """Endpoint DELETE /api/restructurer/restructurations/{id}"""
    try:
        use_cases.delete_restructuration(restructuration_id)
    except Exception as e:
        if type(e).__name__ == "RestructurationNotFoundError":
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
        logger.error(f"Erreur: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erreur interne"
        )


# ===== ENDPOINTS MODULES =====

@router.get(
    "/documents/{document_id}/modules/{module}",
    response_model=ModuleContentResponse,
    summary="Récupérer le contenu d'un module",
    description="Récupère tous les items d'un module restructuré"
)
def get_module_content(
    document_id: str,
    module: str,
    use_cases: RestructurerUseCasesDep
) -> ModuleContentResponse:
    """Endpoint GET /api/restructurer/documents/{id}/modules/{module}"""
    try:
        items = use_cases.get_module_content(document_id, module)
        return ModuleContentResponse(
            module=module,
            items=items,
            total=len(items)
        )
    except Exception as e:
        error_type = type(e).__name__
        if error_type in ["DocumentNotFoundError", "ModuleNotFoundError"]:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
        logger.error(f"Erreur: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erreur interne"
        )


@router.get(
    "/documents/{document_id}/modules/{module}/{item_id}",
    summary="Récupérer un item spécifique",
    description="Récupère un item d'un module"
)
def get_module_item(
    document_id: str,
    module: str,
    item_id: str,
    use_cases: RestructurerUseCasesDep
) -> dict:
    """Endpoint GET /api/restructurer/documents/{id}/modules/{module}/{item_id}"""
    try:
        return use_cases.get_module_item(document_id, module, item_id)
    except Exception as e:
        if type(e).__name__ == "ItemNotFoundError":
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
        logger.error(f"Erreur: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erreur interne"
        )
