"""
Port primaire pour les cas d'usage de l'Analyste.

Interface définissant les opérations disponibles pour l'analyse
de documents dans le pipeline.
"""
from abc import ABC, abstractmethod
from typing import Optional


class AnalyzeDocumentUseCase(ABC):
    """
    Interface des cas d'usage pour l'Analyste.

    RÈGLE: Utilise uniquement des types primitifs (dict, str, int).
    L'analyste évalue un document selon les modules disponibles.
    """

    @abstractmethod
    def list_documents(self) -> list[dict]:
        """
        Liste tous les documents disponibles dans sources/.

        Returns:
            Liste de dicts contenant les métadonnées des documents:
                - id: Identifiant unique
                - name: Nom du fichier
                - path: Chemin relatif
                - size_bytes: Taille
                - created_at: Date de création
                - has_analysis: True si déjà analysé
        """
        pass

    @abstractmethod
    def get_document(self, document_id: str) -> dict:
        """
        Récupère les détails d'un document.

        Args:
            document_id: Identifiant unique du document

        Returns:
            Dict contenant les métadonnées complètes

        Raises:
            DocumentNotFoundError: Si le document n'existe pas
        """
        pass

    @abstractmethod
    def analyze_document(
        self,
        document_id: str,
        force: bool = False
    ) -> dict:
        """
        Lance l'analyse d'un document.

        L'analyste évalue le document selon tous les modules disponibles
        et recommande ceux qui sont pertinents pour le restructureur.

        Args:
            document_id: Identifiant unique du document
            force: Si True, relance l'analyse même si elle existe déjà

        Returns:
            Dict contenant le résultat de l'analyse:
                - id: Identifiant de l'analyse
                - document_id: Identifiant du document
                - summary: Résumé du document
                - module_evaluations: Évaluations par module
                - recommended_modules: Modules recommandés
                - analyzed_at: Date de l'analyse

        Raises:
            DocumentNotFoundError: Si le document n'existe pas
            AnalysisAlreadyExistsError: Si force=False et analyse existe
            AIError: Si l'appel à l'IA échoue
        """
        pass

    @abstractmethod
    def get_analysis(self, analysis_id: str) -> dict:
        """
        Récupère les résultats d'une analyse.

        Args:
            analysis_id: Identifiant de l'analyse

        Returns:
            Dict contenant les résultats complets de l'analyse

        Raises:
            AnalysisNotFoundError: Si l'analyse n'existe pas
        """
        pass

    @abstractmethod
    def get_analysis_by_document(self, document_id: str) -> Optional[dict]:
        """
        Récupère l'analyse d'un document spécifique.

        Args:
            document_id: Identifiant du document

        Returns:
            Dict contenant les résultats ou None si pas d'analyse
        """
        pass

    @abstractmethod
    def list_analyses(self) -> list[dict]:
        """
        Liste toutes les analyses existantes.

        Returns:
            Liste de dicts contenant les résumés des analyses
        """
        pass

    @abstractmethod
    def get_available_modules(self) -> list[dict]:
        """
        Retourne la liste des modules disponibles.

        Returns:
            Liste de dicts décrivant chaque module:
                - id: Identifiant du module
                - name: Nom lisible
                - description: Description du module
        """
        pass

    @abstractmethod
    def delete_analysis(self, analysis_id: str) -> bool:
        """
        Supprime une analyse existante.

        Args:
            analysis_id: Identifiant de l'analyse

        Returns:
            True si supprimée

        Raises:
            AnalysisNotFoundError: Si l'analyse n'existe pas
        """
        pass
