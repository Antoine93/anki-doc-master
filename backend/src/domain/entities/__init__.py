"""
Entités du domaine pour le pipeline Anki.

Ce module expose les entités métier principales utilisées
dans tout le pipeline de génération de cartes.
"""
from src.domain.entities.analysis import Analysis
from src.domain.entities.content_module import ContentModule
from src.domain.entities.document import Document

__all__ = [
    "Analysis",
    "ContentModule",
    "Document",
]
