"""
Port primaire pour le Générateur de cartes.

Interface définissant les cas d'usage pour la génération
de cartes Anki à partir du contenu restructuré.
"""
from abc import ABC, abstractmethod


class GenerateCardsUseCase(ABC):
    """
    Interface des cas d'usage pour le Générateur.

    RÈGLE: Utilise uniquement des types primitifs (dict, str, int).
    """

    @abstractmethod
    def generate_cards(
        self,
        restructuration_id: str,
        card_type: str = "basic",
        modules: list[str] | None = None,
        force: bool = False
    ) -> dict:
        """
        Génère des cartes Anki à partir d'une restructuration.

        Le service récupère la restructuration, extrait les modules
        et génère des cartes selon le type demandé.

        Args:
            restructuration_id: Identifiant de la restructuration source
            card_type: Type de carte ("basic" ou "cloze")
            modules: Liste des modules à traiter. Si None, tous les modules
                     sauf images_list et images_descriptions (exclus par défaut)
            force: Forcer la re-génération si elle existe

        Returns:
            Dict contenant:
                - id: Identifiant de la génération
                - restructuration_id: Identifiant de la restructuration source
                - document_id: Identifiant du document
                - card_type: Type de carte généré
                - modules_processed: Liste des modules traités
                - cards_count: Nombre de cartes par module
                - total_cards: Nombre total de cartes
                - generated_at: Date de génération

        Raises:
            RestructurationNotFoundError: Si la restructuration n'existe pas
            DomainValidationError: Si le type de carte est invalide
            GenerationAlreadyExistsError: Si déjà généré (et force=False)
            AIError: Si l'appel IA échoue
        """
        pass

    @abstractmethod
    def get_generation(self, generation_id: str) -> dict:
        """
        Récupère les détails d'une génération.

        Args:
            generation_id: Identifiant de la génération

        Returns:
            Dict avec les détails de la génération

        Raises:
            GenerationNotFoundError: Si non trouvée
        """
        pass

    @abstractmethod
    def get_generation_by_restructuration(
        self,
        restructuration_id: str,
        card_type: str | None = None
    ) -> dict | None:
        """
        Récupère la génération d'une restructuration.

        Args:
            restructuration_id: Identifiant de la restructuration
            card_type: Filtrer par type de carte (optionnel)

        Returns:
            Dict ou None si pas de génération
        """
        pass

    @abstractmethod
    def get_cards(
        self,
        generation_id: str,
        module: str | None = None
    ) -> list[dict]:
        """
        Récupère les cartes d'une génération.

        Args:
            generation_id: Identifiant de la génération
            module: Filtrer par module (optionnel)

        Returns:
            Liste des cartes

        Raises:
            GenerationNotFoundError: Si la génération n'existe pas
        """
        pass

    @abstractmethod
    def get_card(self, generation_id: str, card_id: str) -> dict:
        """
        Récupère une carte spécifique.

        Args:
            generation_id: Identifiant de la génération
            card_id: Identifiant de la carte

        Returns:
            Dict avec le contenu de la carte

        Raises:
            CardNotFoundError: Si la carte n'existe pas
        """
        pass

    @abstractmethod
    def list_generations(
        self,
        document_id: str | None = None
    ) -> list[dict]:
        """
        Liste les générations.

        Args:
            document_id: Filtrer par document (optionnel)

        Returns:
            Liste des générations
        """
        pass

    @abstractmethod
    def delete_generation(self, generation_id: str) -> bool:
        """
        Supprime une génération et ses cartes.

        Args:
            generation_id: Identifiant de la génération

        Returns:
            True si la suppression a réussi

        Raises:
            GenerationNotFoundError: Si non trouvée
        """
        pass
