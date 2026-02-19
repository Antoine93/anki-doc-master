"""
Conteneur d'injection de dépendances.

Centralise la création et le câblage de toutes les dépendances
de l'application.

ARCHITECTURE:
- Services utilisent des Ports (interfaces)
- DI Container câble les Adapters (implémentations) aux Ports
"""
from pathlib import Path
from functools import lru_cache

from src.ports.primary.analyze_document_use_case import AnalyzeDocumentUseCase
from src.ports.primary.restructure_document_use_case import RestructureDocumentUseCase
from src.ports.primary.generate_cards_use_case import GenerateCardsUseCase
from src.ports.primary.optimize_cards_use_case import OptimizeCardsUseCase
from src.ports.primary.format_cards_use_case import FormatCardsUseCase
from src.domain.services.analyst_service import AnalystService
from src.domain.services.restructurer_service import RestructurerService
from src.domain.services.generator_service import GeneratorService
from src.domain.services.atomizer_service import AtomizerService
from src.domain.services.formatter_service import FormatterService
from src.adapters.secondary.repositories.filesystem_document_repository import (
    FileSystemDocumentRepository
)
from src.adapters.secondary.storage.json_file_analysis_storage import (
    JsonFileAnalysisStorage
)
from src.adapters.secondary.storage.json_restructured_storage import (
    JsonRestructuredStorage
)
from src.adapters.secondary.storage.json_cards_storage import (
    JsonCardsStorage
)
from src.adapters.secondary.storage.json_optimized_cards_storage import (
    JsonOptimizedCardsStorage
)
from src.adapters.secondary.storage.anki_formatted_storage import (
    AnkiFormattedStorage
)
from src.adapters.secondary.prompts.filesystem_prompt_repository import (
    FileSystemPromptRepository
)
from src.adapters.secondary.claude.claude_cli_adapter import ClaudeCliAdapter
from src.adapters.secondary.claude.claude_session_adapter import ClaudeSessionAdapter


def get_project_root() -> Path:
    """Retourne le chemin racine du projet."""
    return Path(__file__).parent.parent.parent


def get_sources_path() -> str:
    """Retourne le chemin du dossier sources/."""
    return str(get_project_root() / "sources")


def get_outputs_path() -> str:
    """Retourne le chemin du dossier outputs/."""
    return str(get_project_root() / "outputs")


def get_prompts_path() -> str:
    """Retourne le chemin du dossier prompts/."""
    return str(get_project_root() / "backend" / "prompts")


# ==================== Repositories ====================

@lru_cache()
def get_document_repository() -> FileSystemDocumentRepository:
    """Factory pour le repository de documents."""
    return FileSystemDocumentRepository(
        sources_path=get_sources_path(),
        outputs_path=get_outputs_path()
    )


@lru_cache()
def get_analysis_storage() -> JsonFileAnalysisStorage:
    """Factory pour le storage d'analyses."""
    return JsonFileAnalysisStorage(outputs_path=get_outputs_path())


@lru_cache()
def get_restructured_storage() -> JsonRestructuredStorage:
    """Factory pour le storage du contenu restructuré."""
    return JsonRestructuredStorage(outputs_path=get_outputs_path())


@lru_cache()
def get_cards_storage() -> JsonCardsStorage:
    """Factory pour le storage des cartes générées."""
    return JsonCardsStorage(outputs_path=get_outputs_path())


@lru_cache()
def get_optimized_cards_storage() -> JsonOptimizedCardsStorage:
    """Factory pour le storage des cartes optimisées."""
    return JsonOptimizedCardsStorage(outputs_path=get_outputs_path())


@lru_cache()
def get_formatted_storage() -> AnkiFormattedStorage:
    """Factory pour le storage des fichiers Anki formatés."""
    return AnkiFormattedStorage(outputs_path=get_outputs_path())


@lru_cache()
def get_prompt_repository() -> FileSystemPromptRepository:
    """Factory pour le repository de prompts."""
    return FileSystemPromptRepository(prompts_path=get_prompts_path())


# ==================== IA ====================

@lru_cache()
def get_ai() -> ClaudeSessionAdapter:
    """
    Factory pour la communication IA.

    Retourne un singleton avec session persistante.
    Le session_id est capturé au premier appel et réutilisé.
    """
    return ClaudeSessionAdapter(timeout=300, working_dir=str(get_project_root()))


def get_ai_legacy() -> ClaudeCliAdapter:
    """Factory pour l'ancien adapter one-shot (fallback)."""
    return ClaudeCliAdapter(timeout=300, working_dir=str(get_project_root()))


# ==================== Services ====================

def get_analyst_service() -> AnalyzeDocumentUseCase:
    """Factory pour le service Analyste."""
    return AnalystService(
        document_repository=get_document_repository(),
        analysis_storage=get_analysis_storage(),
        prompt_repository=get_prompt_repository(),
        ai=get_ai()
    )


def get_restructurer_service() -> RestructureDocumentUseCase:
    """Factory pour le service Restructurateur."""
    return RestructurerService(
        document_repository=get_document_repository(),
        restructured_storage=get_restructured_storage(),
        prompt_repository=get_prompt_repository(),
        ai=get_ai(),
        analysis_storage=get_analysis_storage()
    )


def get_generator_service() -> GenerateCardsUseCase:
    """Factory pour le service Générateur de cartes."""
    return GeneratorService(
        restructured_storage=get_restructured_storage(),
        cards_storage=get_cards_storage(),
        prompt_repository=get_prompt_repository(),
        ai=get_ai()
    )


def get_atomizer_service() -> OptimizeCardsUseCase:
    """Factory pour le service Atomizer (Optimiseur SuperMemo)."""
    return AtomizerService(
        cards_storage=get_cards_storage(),
        optimized_storage=get_optimized_cards_storage(),
        prompt_repository=get_prompt_repository(),
        ai=get_ai()
    )


def get_formatter_service() -> FormatCardsUseCase:
    """Factory pour le service Formatter (Export Anki)."""
    return FormatterService(
        optimized_storage=get_optimized_cards_storage(),
        formatted_storage=get_formatted_storage(),
        prompt_repository=get_prompt_repository(),
        ai=get_ai()
    )
