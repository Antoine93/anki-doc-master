"""
Port secondaire pour le stockage du contenu restructuré.

Interface définissant le contrat pour sauvegarder et récupérer
le contenu restructuré par module (JSON files).
"""
from abc import ABC, abstractmethod


class RestructuredStoragePort(ABC):
    """
    Interface pour le stockage du contenu restructuré.

    Structure de stockage:
    outputs/{document_id}/{analysis_id}/
    ├── modules.json          # Analyse (créé par AnalysisStorage)
    ├── restructuration.json  # Métadonnées restructuration
    ├── themes/
    │   ├── theme-1.json
    │   └── theme-2.json
    ├── vocabulary/
    │   ├── term-1.json
    │   └── ...
    └── ...

    Le restructurateur utilise le même analysis_id que l'analyse.
    """

    @abstractmethod
    def save_restructuration_metadata(
        self,
        document_id: str,
        metadata: dict
    ) -> dict:
        """
        Sauvegarde les métadonnées de restructuration.

        Args:
            document_id: Identifiant du document
            metadata: Métadonnées (id, modules_processed, etc.)

        Returns:
            Dict avec les métadonnées sauvegardées
        """
        pass

    @abstractmethod
    def save_module_item(
        self,
        document_id: str,
        module: str,
        item_id: str,
        content: dict
    ) -> str:
        """
        Sauvegarde un item de module.

        Args:
            document_id: Identifiant du document
            module: Nom du module (themes, vocabulary, etc.)
            item_id: Identifiant de l'item (theme-1, term-1, etc.)
            content: Contenu de l'item

        Returns:
            Chemin du fichier créé
        """
        pass

    @abstractmethod
    def get_restructuration_metadata(
        self,
        document_id: str,
        analysis_id: str | None = None
    ) -> dict | None:
        """
        Récupère les métadonnées de restructuration d'un document.

        Args:
            document_id: Identifiant du document
            analysis_id: Optionnel - si None, utilise la dernière analyse
        """
        pass

    @abstractmethod
    def find_by_id(self, restructuration_id: str) -> dict | None:
        """Récupère une restructuration par son ID."""
        pass

    @abstractmethod
    def get_module_items(
        self,
        document_id: str,
        module: str,
        analysis_id: str | None = None
    ) -> list[dict]:
        """
        Récupère tous les items d'un module.

        Args:
            document_id: Identifiant du document
            module: Nom du module
            analysis_id: Optionnel - si None, utilise la dernière analyse
        """
        pass

    @abstractmethod
    def get_module_item(
        self,
        document_id: str,
        module: str,
        item_id: str,
        analysis_id: str | None = None
    ) -> dict | None:
        """
        Récupère un item spécifique.

        Args:
            document_id: Identifiant du document
            module: Nom du module
            item_id: Identifiant de l'item
            analysis_id: Optionnel - si None, utilise la dernière analyse
        """
        pass

    @abstractmethod
    def exists_for_document(self, document_id: str) -> bool:
        """Vérifie si une restructuration existe pour un document."""
        pass

    @abstractmethod
    def find_all(self) -> list[dict]:
        """Liste toutes les restructurations."""
        pass

    @abstractmethod
    def delete(self, document_id: str, analysis_id: str | None = None) -> bool:
        """
        Supprime une restructuration et ses fichiers.

        Args:
            document_id: Identifiant du document
            analysis_id: Optionnel - si None, utilise la dernière analyse
        """
        pass

    @abstractmethod
    def get_output_path(self, document_id: str, analysis_id: str | None = None) -> str:
        """
        Retourne le chemin du dossier output pour un document.

        Args:
            document_id: Identifiant du document
            analysis_id: Optionnel - si None, utilise la dernière analyse
        """
        pass

    # --- Méthodes de tracking pour reprise ---

    @abstractmethod
    def get_tracking(self, document_id: str, analysis_id: str | None = None) -> dict | None:
        """
        Récupère le fichier de tracking.

        Args:
            document_id: Identifiant du document
            analysis_id: Optionnel - si None, utilise la dernière analyse

        Returns:
            Dict avec les données de tracking ou None si inexistant
        """
        pass

    @abstractmethod
    def save_tracking(self, document_id: str, tracking_data: dict) -> dict:
        """
        Sauvegarde le fichier de tracking.

        Args:
            document_id: Identifiant du document
            tracking_data: Données de tracking à sauvegarder

        Returns:
            Dict avec les données sauvegardées
        """
        pass

    @abstractmethod
    def update_module_status(
        self,
        document_id: str,
        module: str,
        status: str,
        items_count: int = 0,
        error: str | None = None
    ) -> dict:
        """
        Met à jour le statut d'un module dans le tracking.

        Args:
            document_id: Identifiant du document
            module: Nom du module
            status: Statut (pending, in_progress, completed, failed)
            items_count: Nombre d'items extraits
            error: Message d'erreur si échec

        Returns:
            Dict avec le tracking mis à jour
        """
        pass

    @abstractmethod
    def update_session_id(self, document_id: str, session_id: str) -> dict:
        """
        Met à jour le session_id Claude dans le tracking.

        Args:
            document_id: Identifiant du document
            session_id: ID de session Claude

        Returns:
            Dict avec le tracking mis à jour
        """
        pass
