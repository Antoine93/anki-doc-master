"""
Port secondaire pour le stockage des analyses.

Interface définissant le contrat pour la sauvegarde et la récupération
des résultats d'analyse en format JSON (dossier outputs/).
"""
from abc import ABC, abstractmethod
from typing import Optional


class AnalysisStoragePort(ABC):
    """
    Interface du storage pour les résultats d'analyse.

    RÈGLE: Utilise uniquement des types primitifs (dict, str, int).

    Structure de stockage:
        outputs/{document_id}/{analysis_id}/modules.json

    L'analysis_id sert à la fois d'identifiant unique et de nom de dossier.
    Cela permet plusieurs analyses du même document (historique).
    """

    @abstractmethod
    def save(self, analysis_data: dict) -> dict:
        """
        Sauvegarde un résultat d'analyse.

        Args:
            analysis_data: Dict contenant les données de l'analyse:
                - analysis_id: Identifiant unique de l'analyse (sert aussi de nom de dossier)
                - document_id: Identifiant du document analysé
                - detected_modules: Liste des modules détectés
                - analyzed_at: Date de l'analyse (ISO format)

        Returns:
            Dict contenant les données sauvegardées avec output_path ajouté
        """
        pass

    @abstractmethod
    def find_by_id(self, analysis_id: str) -> Optional[dict]:
        """
        Récupère une analyse par son identifiant.

        Args:
            analysis_id: Identifiant unique de l'analyse

        Returns:
            Dict contenant les données de l'analyse ou None si introuvable
        """
        pass

    @abstractmethod
    def find_by_document_id(self, document_id: str) -> Optional[dict]:
        """
        Récupère l'analyse d'un document spécifique.

        Args:
            document_id: Identifiant du document

        Returns:
            Dict contenant les données de l'analyse ou None si introuvable
        """
        pass

    @abstractmethod
    def find_all(self) -> list[dict]:
        """
        Liste toutes les analyses existantes (dernières analyses par document).

        Returns:
            Liste de dicts contenant les données des analyses
        """
        pass

    @abstractmethod
    def find_all_for_document(self, document_id: str) -> list[dict]:
        """
        Liste toutes les analyses d'un document (historique complet).

        Args:
            document_id: Identifiant du document

        Returns:
            Liste de dicts contenant les données des analyses, triées par date (récent en premier)
        """
        pass

    @abstractmethod
    def exists_for_document(self, document_id: str) -> bool:
        """
        Vérifie si une analyse existe pour un document.

        Args:
            document_id: Identifiant du document

        Returns:
            True si une analyse existe, False sinon
        """
        pass

    @abstractmethod
    def delete(self, analysis_id: str) -> bool:
        """
        Supprime une analyse.

        Args:
            analysis_id: Identifiant de l'analyse

        Returns:
            True si supprimée, False si introuvable
        """
        pass
