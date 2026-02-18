"""
Ports secondaires (interfaces pour les adapters).

Architecture:
- Repositories: DocumentRepositoryPort, AnalysisStoragePort, etc.
- Prompts: PromptRepositoryPort (prompts des spécialistes)
- IA: AIPort (communication technique pure)
"""
from src.ports.secondary.document_repository_port import DocumentRepositoryPort
from src.ports.secondary.analysis_storage_port import AnalysisStoragePort
from src.ports.secondary.restructured_storage_port import RestructuredStoragePort
from src.ports.secondary.prompt_repository_port import PromptRepositoryPort
from src.ports.secondary.ai_port import AIPort

__all__ = [
    # Repositories
    "DocumentRepositoryPort",
    "AnalysisStoragePort",
    "RestructuredStoragePort",
    # Prompts
    "PromptRepositoryPort",
    # IA
    "AIPort",
]
