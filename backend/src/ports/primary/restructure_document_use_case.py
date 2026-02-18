"""
Port primaire pour le Restructurateur.

Interface définissant les cas d'usage pour la restructuration
de documents en JSON par module.
"""
from abc import ABC, abstractmethod


class RestructureDocumentUseCase(ABC):
    """
    Interface des cas d'usage pour le Restructurateur.

    RÈGLE: Utilise uniquement des types primitifs (dict, str, int).
    """

    @abstractmethod
    def restructure_document(
        self,
        analysis_id: str,
        force: bool = False
    ) -> dict:
        """
        Restructure un document à partir d'une analyse existante.

        Le service récupère l'analyse, extrait les detected_modules
        et construit le prompt approprié avant d'invoquer l'IA.

        Args:
            analysis_id: Identifiant de l'analyse à restructurer
            force: Forcer la re-restructuration si elle existe

        Returns:
            Dict contenant:
                - id: Identifiant de la restructuration
                - analysis_id: Identifiant de l'analyse source
                - document_id: Identifiant du document
                - modules_processed: Liste des modules traités
                - output_path: Chemin vers le dossier output
                - restructured_at: Date de restructuration

        Raises:
            AnalysisNotFoundError: Si l'analyse n'existe pas
            DocumentNotFoundError: Si le document n'existe pas
            DomainValidationError: Si aucun module détecté
            RestructurationAlreadyExistsError: Si déjà restructuré
            AIError: Si l'appel IA échoue
        """
        pass

    @abstractmethod
    def get_restructuration(self, restructuration_id: str) -> dict:
        """
        Récupère les détails d'une restructuration.

        Args:
            restructuration_id: Identifiant de la restructuration

        Returns:
            Dict avec les détails de la restructuration

        Raises:
            RestructurationNotFoundError: Si non trouvée
        """
        pass

    @abstractmethod
    def get_restructuration_by_document(self, document_id: str) -> dict | None:
        """
        Récupère la restructuration d'un document.

        Args:
            document_id: Identifiant du document

        Returns:
            Dict ou None si pas de restructuration
        """
        pass

    @abstractmethod
    def get_module_content(
        self,
        document_id: str,
        module: str
    ) -> list[dict]:
        """
        Récupère le contenu restructuré d'un module.

        Args:
            document_id: Identifiant du document
            module: Nom du module (themes, vocabulary, etc.)

        Returns:
            Liste des items du module

        Raises:
            DocumentNotFoundError: Si le document n'existe pas
            ModuleNotFoundError: Si le module n'existe pas
        """
        pass

    @abstractmethod
    def get_module_item(
        self,
        document_id: str,
        module: str,
        item_id: str
    ) -> dict:
        """
        Récupère un item spécifique d'un module.

        Args:
            document_id: Identifiant du document
            module: Nom du module
            item_id: Identifiant de l'item

        Returns:
            Dict avec le contenu de l'item

        Raises:
            ItemNotFoundError: Si l'item n'existe pas
        """
        pass

    @abstractmethod
    def list_restructurations(self) -> list[dict]:
        """Liste toutes les restructurations."""
        pass

    @abstractmethod
    def delete_restructuration(self, restructuration_id: str) -> bool:
        """Supprime une restructuration et ses fichiers."""
        pass
