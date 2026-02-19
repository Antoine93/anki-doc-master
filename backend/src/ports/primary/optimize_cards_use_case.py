"""
Port primaire pour l'Atomizer (Optimiseur SuperMemo).

Interface définissant les cas d'usage pour l'optimisation
des cartes Anki selon les règles SuperMemo.
"""
from abc import ABC, abstractmethod


class OptimizeCardsUseCase(ABC):
    """
    Interface des cas d'usage pour l'Atomizer.

    RÈGLE: Utilise uniquement des types primitifs (dict, str, int).
    """

    @abstractmethod
    def optimize_cards(
        self,
        generation_id: str,
        content_types: list[str] | None = None,
        force: bool = False
    ) -> dict:
        """
        Optimise les cartes d'une génération selon SuperMemo.

        Le service récupère les cartes générées et les optimise
        en appliquant les règles d'atomisation, simplification
        et anti-interférence.

        Args:
            generation_id: Identifiant de la génération source
            content_types: Types de contenu à traiter (general, math_formulas,
                          code, tables, images). Si None, détection auto.
            force: Forcer la ré-optimisation si elle existe

        Returns:
            Dict contenant:
                - id: Identifiant de l'optimisation
                - generation_id: Identifiant de la génération source
                - document_id: Identifiant du document
                - card_type: Type de carte (basic, cloze)
                - cards_input: Nombre de cartes en entrée
                - cards_output: Nombre de cartes en sortie
                - optimization_ratio: Ratio output/input
                - optimized_at: Date d'optimisation

        Raises:
            GenerationNotFoundError: Si la génération n'existe pas
            OptimizationAlreadyExistsError: Si déjà optimisé (et force=False)
            AIError: Si l'appel IA échoue
        """
        pass

    @abstractmethod
    def get_optimization(self, optimization_id: str) -> dict:
        """
        Récupère les détails d'une optimisation.

        Args:
            optimization_id: Identifiant de l'optimisation

        Returns:
            Dict avec les détails de l'optimisation

        Raises:
            OptimizationNotFoundError: Si non trouvée
        """
        pass

    @abstractmethod
    def get_optimization_by_generation(
        self,
        generation_id: str
    ) -> dict | None:
        """
        Récupère l'optimisation d'une génération.

        Args:
            generation_id: Identifiant de la génération

        Returns:
            Dict ou None si pas d'optimisation
        """
        pass

    @abstractmethod
    def get_optimized_cards(
        self,
        optimization_id: str,
        module: str | None = None
    ) -> list[dict]:
        """
        Récupère les cartes optimisées.

        Args:
            optimization_id: Identifiant de l'optimisation
            module: Filtrer par module source (optionnel)

        Returns:
            Liste des cartes optimisées

        Raises:
            OptimizationNotFoundError: Si l'optimisation n'existe pas
        """
        pass

    @abstractmethod
    def get_optimized_card(
        self,
        optimization_id: str,
        card_id: str
    ) -> dict:
        """
        Récupère une carte optimisée spécifique.

        Args:
            optimization_id: Identifiant de l'optimisation
            card_id: Identifiant de la carte

        Returns:
            Dict avec le contenu de la carte

        Raises:
            CardNotFoundError: Si la carte n'existe pas
        """
        pass

    @abstractmethod
    def list_optimizations(
        self,
        document_id: str | None = None
    ) -> list[dict]:
        """
        Liste les optimisations.

        Args:
            document_id: Filtrer par document (optionnel)

        Returns:
            Liste des optimisations
        """
        pass

    @abstractmethod
    def delete_optimization(self, optimization_id: str) -> bool:
        """
        Supprime une optimisation et ses cartes.

        Args:
            optimization_id: Identifiant de l'optimisation

        Returns:
            True si la suppression a réussi

        Raises:
            OptimizationNotFoundError: Si non trouvée
        """
        pass
