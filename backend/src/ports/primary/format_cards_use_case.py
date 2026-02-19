"""
Port primaire pour le Formatter (Export Anki).

Interface définissant les cas d'usage pour le formatage
des cartes optimisées en fichiers .txt importables dans Anki.
"""
from abc import ABC, abstractmethod


class FormatCardsUseCase(ABC):
    """
    Interface des cas d'usage pour le Formatter.

    RÈGLE: Utilise uniquement des types primitifs (dict, str, int).
    """

    @abstractmethod
    def format_cards(
        self,
        optimization_id: str,
        force: bool = False
    ) -> dict:
        """
        Formate les cartes optimisées en fichier Anki .txt.

        Le service récupère les cartes optimisées et les transforme
        en fichier texte avec la syntaxe Anki (headers, séparateurs,
        HTML, LaTeX, cloze).

        Args:
            optimization_id: Identifiant de l'optimisation source
            force: Forcer le re-formatage si déjà existant

        Returns:
            Dict contenant:
                - id: Identifiant du formatage
                - optimization_id: Identifiant de l'optimisation source
                - document_id: Identifiant du document
                - card_type: Type de carte (basic, cloze)
                - cards_count: Nombre de cartes formatées
                - output_file: Chemin du fichier .txt généré
                - formatted_at: Date de formatage

        Raises:
            OptimizationNotFoundError: Si l'optimisation n'existe pas
            FormattingAlreadyExistsError: Si déjà formaté (et force=False)
            AIError: Si l'appel IA échoue
        """
        pass

    @abstractmethod
    def get_formatting(self, formatting_id: str) -> dict:
        """
        Récupère les détails d'un formatage.

        Args:
            formatting_id: Identifiant du formatage

        Returns:
            Dict avec les détails du formatage

        Raises:
            FormattingNotFoundError: Si non trouvé
        """
        pass

    @abstractmethod
    def get_formatting_by_optimization(
        self,
        optimization_id: str
    ) -> dict | None:
        """
        Récupère le formatage d'une optimisation.

        Args:
            optimization_id: Identifiant de l'optimisation

        Returns:
            Dict ou None si pas de formatage
        """
        pass

    @abstractmethod
    def get_formatted_content(self, formatting_id: str) -> str:
        """
        Récupère le contenu du fichier Anki formaté.

        Args:
            formatting_id: Identifiant du formatage

        Returns:
            Contenu texte du fichier .txt Anki

        Raises:
            FormattingNotFoundError: Si le formatage n'existe pas
        """
        pass

    @abstractmethod
    def list_formattings(
        self,
        document_id: str | None = None
    ) -> list[dict]:
        """
        Liste les formatages.

        Args:
            document_id: Filtrer par document (optionnel)

        Returns:
            Liste des formatages
        """
        pass

    @abstractmethod
    def delete_formatting(self, formatting_id: str) -> bool:
        """
        Supprime un formatage et son fichier.

        Args:
            formatting_id: Identifiant du formatage

        Returns:
            True si la suppression a réussi

        Raises:
            FormattingNotFoundError: Si non trouvé
        """
        pass
