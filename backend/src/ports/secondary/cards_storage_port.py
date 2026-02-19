"""
Port secondaire pour le stockage des cartes générées.

Interface définissant le contrat pour sauvegarder et récupérer
les cartes Anki générées.
"""
from abc import ABC, abstractmethod


class CardsStoragePort(ABC):
    """
    Interface pour le stockage des cartes générées.

    Structure de stockage:
    outputs/{document_id}/{analysis_id}/
    ├── cards/
    │   ├── generation.json       # Métadonnées de la génération
    │   ├── tracking.json         # Tracking pour reprise
    │   ├── basic/                # Cartes type basic
    │   │   ├── themes/
    │   │   │   ├── card-1.json
    │   │   │   └── card-2.json
    │   │   └── vocabulary/
    │   │       └── card-1.json
    │   └── cloze/                # Cartes type cloze
    │       └── themes/
    │           └── card-1.json

    Le générateur utilise le même analysis_id que la restructuration.
    """

    @abstractmethod
    def save_generation_metadata(
        self,
        document_id: str,
        card_type: str,
        metadata: dict
    ) -> dict:
        """
        Sauvegarde les métadonnées de génération.

        Args:
            document_id: Identifiant du document
            card_type: Type de carte (basic, cloze)
            metadata: Métadonnées (id, modules_processed, etc.)

        Returns:
            Dict avec les métadonnées sauvegardées
        """
        pass

    @abstractmethod
    def save_card(
        self,
        document_id: str,
        card_type: str,
        module: str,
        card_id: str,
        content: dict
    ) -> str:
        """
        Sauvegarde une carte.

        Args:
            document_id: Identifiant du document
            card_type: Type de carte (basic, cloze)
            module: Nom du module source
            card_id: Identifiant de la carte
            content: Contenu de la carte

        Returns:
            Chemin du fichier créé
        """
        pass

    @abstractmethod
    def get_generation_metadata(
        self,
        document_id: str,
        card_type: str | None = None,
        analysis_id: str | None = None
    ) -> dict | None:
        """
        Récupère les métadonnées de génération.

        Args:
            document_id: Identifiant du document
            card_type: Type de carte (optionnel)
            analysis_id: Optionnel - si None, utilise la dernière analyse
        """
        pass

    @abstractmethod
    def find_by_id(self, generation_id: str) -> dict | None:
        """
        Récupère une génération par son ID.

        Args:
            generation_id: Identifiant de la génération

        Returns:
            Dict avec les métadonnées ou None
        """
        pass

    @abstractmethod
    def get_cards(
        self,
        document_id: str,
        card_type: str,
        module: str | None = None,
        analysis_id: str | None = None
    ) -> list[dict]:
        """
        Récupère les cartes.

        Args:
            document_id: Identifiant du document
            card_type: Type de carte
            module: Filtrer par module (optionnel)
            analysis_id: Optionnel - si None, utilise la dernière analyse
        """
        pass

    @abstractmethod
    def get_card(
        self,
        document_id: str,
        card_type: str,
        module: str,
        card_id: str,
        analysis_id: str | None = None
    ) -> dict | None:
        """
        Récupère une carte spécifique.

        Args:
            document_id: Identifiant du document
            card_type: Type de carte
            module: Nom du module
            card_id: Identifiant de la carte
            analysis_id: Optionnel
        """
        pass

    @abstractmethod
    def exists_for_restructuration(
        self,
        document_id: str,
        card_type: str | None = None
    ) -> bool:
        """
        Vérifie si une génération existe.

        Args:
            document_id: Identifiant du document
            card_type: Type de carte (optionnel)
        """
        pass

    @abstractmethod
    def find_all(self, document_id: str | None = None) -> list[dict]:
        """
        Liste toutes les générations.

        Args:
            document_id: Filtrer par document (optionnel)
        """
        pass

    @abstractmethod
    def delete(
        self,
        document_id: str,
        card_type: str | None = None,
        analysis_id: str | None = None
    ) -> bool:
        """
        Supprime une génération et ses cartes.

        Args:
            document_id: Identifiant du document
            card_type: Type de carte (None = tous les types)
            analysis_id: Optionnel
        """
        pass

    @abstractmethod
    def get_output_path(
        self,
        document_id: str,
        card_type: str,
        analysis_id: str | None = None
    ) -> str:
        """
        Retourne le chemin du dossier de cartes.

        Args:
            document_id: Identifiant du document
            card_type: Type de carte
            analysis_id: Optionnel
        """
        pass

    # --- Méthodes de tracking pour reprise ---

    @abstractmethod
    def get_tracking(
        self,
        document_id: str,
        card_type: str,
        analysis_id: str | None = None
    ) -> dict | None:
        """
        Récupère le fichier de tracking.

        Args:
            document_id: Identifiant du document
            card_type: Type de carte
            analysis_id: Optionnel

        Returns:
            Dict avec les données de tracking ou None
        """
        pass

    @abstractmethod
    def save_tracking(
        self,
        document_id: str,
        card_type: str,
        tracking_data: dict
    ) -> dict:
        """
        Sauvegarde le fichier de tracking.

        Args:
            document_id: Identifiant du document
            card_type: Type de carte
            tracking_data: Données de tracking

        Returns:
            Dict avec les données sauvegardées
        """
        pass

    @abstractmethod
    def update_module_status(
        self,
        document_id: str,
        card_type: str,
        module: str,
        status: str,
        cards_count: int = 0,
        error: str | None = None
    ) -> dict:
        """
        Met à jour le statut d'un module dans le tracking.

        Args:
            document_id: Identifiant du document
            card_type: Type de carte
            module: Nom du module
            status: Statut (pending, in_progress, completed, failed)
            cards_count: Nombre de cartes générées
            error: Message d'erreur si échec

        Returns:
            Dict avec le tracking mis à jour
        """
        pass

    @abstractmethod
    def update_session_id(
        self,
        document_id: str,
        card_type: str,
        session_id: str
    ) -> dict:
        """
        Met à jour le session_id Claude dans le tracking.

        Args:
            document_id: Identifiant du document
            card_type: Type de carte
            session_id: ID de session Claude

        Returns:
            Dict avec le tracking mis à jour
        """
        pass
