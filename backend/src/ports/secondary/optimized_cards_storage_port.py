"""
Port secondaire pour le stockage des cartes optimisées.

Interface définissant le contrat pour sauvegarder et récupérer
les cartes optimisées par l'Atomizer.
"""
from abc import ABC, abstractmethod


class OptimizedCardsStoragePort(ABC):
    """
    Interface pour le stockage des cartes optimisées.

    Structure de stockage:
    outputs/{document_id}/{analysis_id}/
    ├── cards/
    │   ├── basic/                    # Cartes générées
    │   └── optimized/                # Cartes optimisées
    │       ├── optimization.json     # Métadonnées
    │       ├── tracking.json         # Tracking pour reprise
    │       └── basic/                # Type de carte source
    │           ├── themes/
    │           │   ├── card-1.json
    │           │   └── card-2.json
    │           └── vocabulary/
    │               └── card-1.json

    L'optimiseur crée un sous-dossier 'optimized' dans cards/.
    """

    @abstractmethod
    def save_optimization_metadata(
        self,
        document_id: str,
        card_type: str,
        metadata: dict
    ) -> dict:
        """
        Sauvegarde les métadonnées d'optimisation.

        Args:
            document_id: Identifiant du document
            card_type: Type de carte source (basic, cloze)
            metadata: Métadonnées (id, cards_input, cards_output, etc.)

        Returns:
            Dict avec les métadonnées sauvegardées
        """
        pass

    @abstractmethod
    def save_optimized_card(
        self,
        document_id: str,
        card_type: str,
        module: str,
        card_id: str,
        content: dict
    ) -> str:
        """
        Sauvegarde une carte optimisée.

        Args:
            document_id: Identifiant du document
            card_type: Type de carte (basic, cloze)
            module: Nom du module source
            card_id: Identifiant de la carte
            content: Contenu de la carte optimisée

        Returns:
            Chemin du fichier créé
        """
        pass

    @abstractmethod
    def get_optimization_metadata(
        self,
        document_id: str,
        card_type: str | None = None,
        analysis_id: str | None = None
    ) -> dict | None:
        """
        Récupère les métadonnées d'optimisation.

        Args:
            document_id: Identifiant du document
            card_type: Type de carte (optionnel)
            analysis_id: Optionnel - si None, utilise la dernière analyse
        """
        pass

    @abstractmethod
    def find_by_id(self, optimization_id: str) -> dict | None:
        """
        Récupère une optimisation par son ID.

        Args:
            optimization_id: Identifiant de l'optimisation

        Returns:
            Dict avec les métadonnées ou None
        """
        pass

    @abstractmethod
    def get_optimized_cards(
        self,
        document_id: str,
        card_type: str,
        module: str | None = None,
        analysis_id: str | None = None
    ) -> list[dict]:
        """
        Récupère les cartes optimisées.

        Args:
            document_id: Identifiant du document
            card_type: Type de carte
            module: Filtrer par module (optionnel)
            analysis_id: Optionnel
        """
        pass

    @abstractmethod
    def get_optimized_card(
        self,
        document_id: str,
        card_type: str,
        module: str,
        card_id: str,
        analysis_id: str | None = None
    ) -> dict | None:
        """
        Récupère une carte optimisée spécifique.

        Args:
            document_id: Identifiant du document
            card_type: Type de carte
            module: Nom du module
            card_id: Identifiant de la carte
            analysis_id: Optionnel
        """
        pass

    @abstractmethod
    def exists_for_generation(
        self,
        document_id: str,
        card_type: str | None = None
    ) -> bool:
        """
        Vérifie si une optimisation existe.

        Args:
            document_id: Identifiant du document
            card_type: Type de carte (optionnel)
        """
        pass

    @abstractmethod
    def find_all(self, document_id: str | None = None) -> list[dict]:
        """
        Liste toutes les optimisations.

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
        Supprime une optimisation et ses cartes.

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
        Retourne le chemin du dossier de cartes optimisées.

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
        cards_input: int = 0,
        cards_output: int = 0,
        error: str | None = None
    ) -> dict:
        """
        Met à jour le statut d'un module dans le tracking.

        Args:
            document_id: Identifiant du document
            card_type: Type de carte
            module: Nom du module
            status: Statut (pending, in_progress, completed, failed)
            cards_input: Nombre de cartes en entrée
            cards_output: Nombre de cartes en sortie
            error: Message d'erreur si échec

        Returns:
            Dict avec le tracking mis à jour
        """
        pass
