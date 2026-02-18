"""
Router FastAPI pour l'Analyste.

Expose les endpoints HTTP pour l'analyse de documents.
"""
import logging
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status

from src.adapters.primary.fastapi.schemas import (
    DocumentResponse,
    DocumentListResponse,
    AnalysisResponse,
    AnalysisListResponse,
    AnalyzeDocumentRequest,
    ModuleResponse,
    ModuleListResponse
)
from src.ports.primary.analyze_document_use_case import AnalyzeDocumentUseCase


logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/analyst",
    tags=["Analyst"]
)


def get_analyst_use_cases() -> AnalyzeDocumentUseCase:
    """Injection du service Analyste."""
    from src.di_container import get_analyst_service
    return get_analyst_service()


AnalystUseCasesDep = Annotated[AnalyzeDocumentUseCase, Depends(get_analyst_use_cases)]


# ===== ENDPOINTS DOCUMENTS =====

@router.get(
    "/documents",
    response_model=DocumentListResponse,
    summary="Lister les documents",
    description="Liste tous les documents PDF disponibles dans sources/"
)
def list_documents(use_cases: AnalystUseCasesDep) -> DocumentListResponse:
    """Endpoint GET /api/analyst/documents"""
    try:
        documents = use_cases.list_documents()
        return DocumentListResponse(
            documents=[DocumentResponse(**doc) for doc in documents],
            total=len(documents)
        )
    except Exception as e:
        logger.error(f"Erreur listing documents: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erreur interne"
        )


@router.get(
    "/documents/{document_id}",
    response_model=DocumentResponse,
    summary="Récupérer un document",
    description="Récupère les détails d'un document"
)
def get_document(document_id: str, use_cases: AnalystUseCasesDep) -> DocumentResponse:
    """Endpoint GET /api/analyst/documents/{document_id}"""
    try:
        document = use_cases.get_document(document_id)
        return DocumentResponse(**document)
    except Exception as e:
        if type(e).__name__ == "DocumentNotFoundError":
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
        logger.error(f"Erreur récupération document: {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Erreur interne")


# ===== ENDPOINTS ANALYSES =====

@router.post(
    "/analyses",
    response_model=AnalysisResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Analyser un document",
    description="Détecte les modules présents dans un document PDF"
)
def analyze_document(request: AnalyzeDocumentRequest, use_cases: AnalystUseCasesDep) -> AnalysisResponse:
    """Endpoint POST /api/analyst/analyses"""
    try:
        analysis = use_cases.analyze_document(
            document_id=request.document_id,
            force=request.force
        )
        return AnalysisResponse(**analysis)

    except Exception as e:
        error_type = type(e).__name__

        if error_type == "DocumentNotFoundError":
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
        elif error_type == "AnalysisAlreadyExistsError":
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))
        elif error_type == "AIError":
            logger.error(f"Erreur IA: {e}", exc_info=True)
            raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(e))

        logger.error(f"Erreur analyse document: {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Erreur interne")


@router.get(
    "/analyses",
    response_model=AnalysisListResponse,
    summary="Lister les analyses",
    description="Liste toutes les analyses existantes"
)
def list_analyses(use_cases: AnalystUseCasesDep) -> AnalysisListResponse:
    """Endpoint GET /api/analyst/analyses"""
    try:
        analyses = use_cases.list_analyses()
        return AnalysisListResponse(
            analyses=[AnalysisResponse(**a) for a in analyses],
            total=len(analyses)
        )
    except Exception as e:
        logger.error(f"Erreur listing analyses: {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Erreur interne")


@router.get(
    "/analyses/{analysis_id}",
    response_model=AnalysisResponse,
    summary="Récupérer une analyse",
    description="Récupère les modules détectés d'une analyse"
)
def get_analysis(analysis_id: str, use_cases: AnalystUseCasesDep) -> AnalysisResponse:
    """Endpoint GET /api/analyst/analyses/{analysis_id}"""
    try:
        analysis = use_cases.get_analysis(analysis_id)
        return AnalysisResponse(**analysis)
    except Exception as e:
        if type(e).__name__ == "AnalysisNotFoundError":
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
        logger.error(f"Erreur récupération analyse: {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Erreur interne")


@router.get(
    "/documents/{document_id}/analysis",
    response_model=AnalysisResponse,
    summary="Récupérer l'analyse d'un document",
    description="Récupère l'analyse associée à un document"
)
def get_document_analysis(document_id: str, use_cases: AnalystUseCasesDep) -> AnalysisResponse:
    """Endpoint GET /api/analyst/documents/{document_id}/analysis"""
    try:
        analysis = use_cases.get_analysis_by_document(document_id)
        if analysis is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Aucune analyse pour le document {document_id}"
            )
        return AnalysisResponse(**analysis)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erreur récupération analyse: {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Erreur interne")


@router.delete(
    "/analyses/{analysis_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Supprimer une analyse",
    description="Supprime une analyse existante"
)
def delete_analysis(analysis_id: str, use_cases: AnalystUseCasesDep) -> None:
    """Endpoint DELETE /api/analyst/analyses/{analysis_id}"""
    try:
        use_cases.delete_analysis(analysis_id)
    except Exception as e:
        if type(e).__name__ == "AnalysisNotFoundError":
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
        logger.error(f"Erreur suppression analyse: {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Erreur interne")


# ===== ENDPOINTS MODULES =====

@router.get(
    "/modules",
    response_model=ModuleListResponse,
    summary="Lister les modules",
    description="Liste tous les modules de contenu disponibles"
)
def list_modules(use_cases: AnalystUseCasesDep) -> ModuleListResponse:
    """Endpoint GET /api/analyst/modules"""
    try:
        modules = use_cases.get_available_modules()
        return ModuleListResponse(modules=[ModuleResponse(**m) for m in modules])
    except Exception as e:
        logger.error(f"Erreur listing modules: {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Erreur interne")
