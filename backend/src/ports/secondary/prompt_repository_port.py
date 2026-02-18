"""
Port secondaire pour les prompts des spécialistes.

Interface pour récupérer les prompts métier utilisés par les services.
Les prompts sont des données externes qui peuvent changer.

Structure attendue:
prompts/
├── analyst/
│   └── system.md
├── restructurer/
│   ├── system.md
│   └── modules/
│       ├── themes.md
│       └── ...
"""
from abc import ABC, abstractmethod


class PromptRepositoryPort(ABC):
    """
    Interface pour le repository de prompts.

    Les prompts sont organisés par spécialiste:
    - Chaque spécialiste a un dossier
    - Chaque dossier contient un system.md (prompt principal)
    - Optionnellement un sous-dossier modules/ pour les sous-prompts

    Supporte le lazy loading: les prompts sont chargés à la demande.
    """

    @abstractmethod
    def get_system_prompt(self, specialist_id: str) -> str:
        """
        Récupère le prompt système d'un spécialiste.

        Args:
            specialist_id: Identifiant du spécialiste (ex: "analyst", "restructurer")

        Returns:
            Le contenu du prompt système

        Raises:
            PromptNotFoundError: Si le prompt n'existe pas
        """
        pass

    @abstractmethod
    def get_module_prompt(self, specialist_id: str, module_id: str) -> str:
        """
        Récupère le prompt d'un module pour un spécialiste.

        Args:
            specialist_id: Identifiant du spécialiste
            module_id: Identifiant du module (ex: "themes", "vocabulary")

        Returns:
            Le contenu du prompt du module

        Raises:
            PromptNotFoundError: Si le prompt n'existe pas
        """
        pass

    @abstractmethod
    def list_specialists(self) -> list[str]:
        """
        Liste tous les spécialistes disponibles.

        Returns:
            Liste des identifiants de spécialistes
        """
        pass

    @abstractmethod
    def list_modules(self, specialist_id: str) -> list[str]:
        """
        Liste tous les modules disponibles pour un spécialiste.

        Args:
            specialist_id: Identifiant du spécialiste

        Returns:
            Liste des identifiants de modules
        """
        pass

    @abstractmethod
    def save_system_prompt(self, specialist_id: str, content: str) -> None:
        """
        Sauvegarde ou met à jour le prompt système d'un spécialiste.

        Args:
            specialist_id: Identifiant du spécialiste
            content: Contenu du prompt
        """
        pass

    @abstractmethod
    def save_module_prompt(
        self,
        specialist_id: str,
        module_id: str,
        content: str
    ) -> None:
        """
        Sauvegarde ou met à jour le prompt d'un module.

        Args:
            specialist_id: Identifiant du spécialiste
            module_id: Identifiant du module
            content: Contenu du prompt
        """
        pass
