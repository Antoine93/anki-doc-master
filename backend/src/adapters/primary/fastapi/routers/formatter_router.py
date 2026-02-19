"""
Router FastAPI pour le Formatter (Export Anki).

Expose les endpoints HTTP pour le formatage des cartes
optimisées en fichiers .txt importables dans Anki.
"""
import logging
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status, Query
from fastapi.responses import PlainTextResponse

from src.adapters.primary.fastapi.schemas.formatter_schemas import (
    FormatCardsRequest,
    FormattingResponse,
    FormattingListResponse,
    FormattedContentResponse
)
from src.ports.primary.format_cards_use_case import FormatCardsUseCase


logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/formatter",
    tags=["Formatter"]
)


def get_formatter_use_cases() -> FormatCardsUseCase:
    """Injection du service Formatter."""
    from src.di_container import get_formatter_service
    return get_formatter_service()


FormatterUseCasesDep = Annotated[
    FormatCardsUseCase,
    Depends(get_formatter_use_cases)
]


# ===== ENDPOINTS FORMATAGE =====

@router.post(
    "/formattings",
    response_model=FormattingResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Formater des cartes pour Anki",
    description="Transforme les cartes optimisées en fichier .txt importable "
                "dans Anki avec headers, HTML et syntaxe appropriée."
)
def format_cards(
    request: FormatCardsRequest,
    use_cases: FormatterUseCasesDep
) -> FormattingResponse:
    """Endpoint POST /api/formatter/formattings"""
    try:
        result = use_cases.format_cards(
            optimization_id=request.optimization_id,
            force=request.force
        )
        return FormattingResponse(**result)

    except Exception as e:
        error_type = type(e).__name__

        if error_type == "OptimizationNotFoundError":
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=str(e)
            )
        elif error_type == "FormattingAlreadyExistsError":
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=str(e)
            )
        elif error_type == "DomainValidationError":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(e)
            )
        elif error_type == "AIError":
            logger.error(f"Erreur IA: {e}", exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail=str(e)
            )

        logger.error(f"Erreur formatage: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erreur interne"
        )


@router.get(
    "/formattings",
    response_model=FormattingListResponse,
    summary="Lister les formatages",
    description="Liste tous les fichiers Anki formatés existants"
)
def list_formattings(
    use_cases: FormatterUseCasesDep,
    document_id: str | None = Query(None, description="Filtrer par document")
) -> FormattingListResponse:
    """Endpoint GET /api/formatter/formattings"""
    try:
        formattings = use_cases.list_formattings(document_id)
        return FormattingListResponse(
            formattings=[FormattingResponse(**f) for f in formattings],
            total=len(formattings)
        )
    except Exception as e:
        logger.error(f"Erreur listing: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erreur interne"
        )


@router.get(
    "/formattings/{formatting_id}",
    response_model=FormattingResponse,
    summary="Récupérer un formatage",
    description="Récupère les détails d'un formatage Anki"
)
def get_formatting(
    formatting_id: str,
    use_cases: FormatterUseCasesDep
) -> FormattingResponse:
    """Endpoint GET /api/formatter/formattings/{id}"""
    try:
        result = use_cases.get_formatting(formatting_id)
        return FormattingResponse(**result)
    except Exception as e:
        if type(e).__name__ == "FormattingNotFoundError":
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=str(e)
            )
        logger.error(f"Erreur: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erreur interne"
        )


@router.get(
    "/optimizations/{optimization_id}/formatting",
    response_model=FormattingResponse,
    summary="Récupérer le formatage d'une optimisation",
    description="Récupère le formatage associé à une optimisation de cartes"
)
def get_optimization_formatting(
    optimization_id: str,
    use_cases: FormatterUseCasesDep
) -> FormattingResponse:
    """Endpoint GET /api/formatter/optimizations/{id}/formatting"""
    try:
        result = use_cases.get_formatting_by_optimization(optimization_id)
        if result is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Aucun formatage pour l'optimisation {optimization_id}"
            )
        return FormattingResponse(**result)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erreur: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erreur interne"
        )


@router.delete(
    "/formattings/{formatting_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Supprimer un formatage",
    description="Supprime un formatage et son fichier Anki"
)
def delete_formatting(
    formatting_id: str,
    use_cases: FormatterUseCasesDep
) -> None:
    """Endpoint DELETE /api/formatter/formattings/{id}"""
    try:
        use_cases.delete_formatting(formatting_id)
    except Exception as e:
        if type(e).__name__ == "FormattingNotFoundError":
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=str(e)
            )
        logger.error(f"Erreur: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erreur interne"
        )


# ===== ENDPOINTS CONTENU =====

@router.get(
    "/formattings/{formatting_id}/content",
    response_model=FormattedContentResponse,
    summary="Récupérer le contenu formaté",
    description="Récupère le contenu du fichier Anki .txt (JSON)"
)
def get_formatted_content(
    formatting_id: str,
    use_cases: FormatterUseCasesDep
) -> FormattedContentResponse:
    """Endpoint GET /api/formatter/formattings/{id}/content"""
    try:
        formatting = use_cases.get_formatting(formatting_id)
        content = use_cases.get_formatted_content(formatting_id)

        return FormattedContentResponse(
            formatting_id=formatting_id,
            card_type=formatting["card_type"],
            content=content,
            lines_count=len(content.strip().split("\n"))
        )
    except Exception as e:
        error_type = type(e).__name__
        if error_type == "FormattingNotFoundError":
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=str(e)
            )
        logger.error(f"Erreur: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erreur interne"
        )


@router.get(
    "/formattings/{formatting_id}/download",
    response_class=PlainTextResponse,
    summary="Télécharger le fichier Anki",
    description="Télécharge le fichier .txt Anki directement"
)
def download_formatted_file(
    formatting_id: str,
    use_cases: FormatterUseCasesDep
) -> PlainTextResponse:
    """Endpoint GET /api/formatter/formattings/{id}/download"""
    try:
        formatting = use_cases.get_formatting(formatting_id)
        content = use_cases.get_formatted_content(formatting_id)

        filename = f"{formatting['document_name']}_{formatting['card_type']}.txt"

        return PlainTextResponse(
            content=content,
            media_type="text/plain; charset=utf-8",
            headers={
                "Content-Disposition": f'attachment; filename="{filename}"'
            }
        )
    except Exception as e:
        error_type = type(e).__name__
        if error_type == "FormattingNotFoundError":
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=str(e)
            )
        logger.error(f"Erreur: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erreur interne"
        )
