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
from src.domain.services.analyst_service import AnalystService
from src.domain.services.restructurer_service import RestructurerService
from src.adapters.secondary.repositories.filesystem_document_repository import (
    FileSystemDocumentRepository
)
from src.adapters.secondary.storage.json_file_analysis_storage import (
    JsonFileAnalysisStorage
)
from src.adapters.secondary.storage.json_restructured_storage import (
    JsonRestructuredStorage
)
from src.adapters.secondary.prompts.filesystem_prompt_repository import (
    FileSystemPromptRepository
)
from src.adapters.secondary.claude.claude_cli_adapter import ClaudeCliAdapter


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
def get_prompt_repository() -> FileSystemPromptRepository:
    """Factory pour le repository de prompts."""
    return FileSystemPromptRepository(prompts_path=get_prompts_path())


# ==================== IA ====================

@lru_cache()
def get_ai() -> ClaudeCliAdapter:
    """Factory pour la communication IA."""
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
