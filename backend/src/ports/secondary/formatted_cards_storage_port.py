"""
Port secondaire pour le stockage des fichiers Anki formatés.

Interface définissant le contrat pour sauvegarder et récupérer
les fichiers .txt générés par le Formatter.
"""
from abc import ABC, abstractmethod


class FormattedCardsStoragePort(ABC):
    """
    Interface pour le stockage des fichiers Anki formatés.

    Structure de stockage:
    outputs/{document_id}/{analysis_id}/
    ├── cards/
    │   ├── optimized/            # Cartes optimisées (source)
    │   └── anki/                 # Fichiers Anki exportés
    │       ├── formatting.json   # Métadonnées
    │       ├── basic.txt         # Cartes basic formatées
    │       └── cloze.txt         # Cartes cloze formatées

    Le formatter crée un sous-dossier 'anki' dans cards/.
    """

    @abstractmethod
    def save_formatting_metadata(
        self,
        document_id: str,
        card_type: str,
        metadata: dict
    ) -> dict:
        """
        Sauvegarde les métadonnées de formatage.

        Args:
            document_id: Identifiant du document
            card_type: Type de carte (basic, cloze)
            metadata: Métadonnées (id, cards_count, etc.)

        Returns:
            Dict avec les métadonnées sauvegardées
        """
        pass

    @abstractmethod
    def save_formatted_file(
        self,
        document_id: str,
        card_type: str,
        content: str
    ) -> str:
        """
        Sauvegarde le fichier Anki formaté.

        Args:
            document_id: Identifiant du document
            card_type: Type de carte (basic, cloze)
            content: Contenu texte du fichier Anki

        Returns:
            Chemin du fichier créé
        """
        pass

    @abstractmethod
    def get_formatting_metadata(
        self,
        document_id: str,
        card_type: str | None = None,
        analysis_id: str | None = None
    ) -> dict | None:
        """
        Récupère les métadonnées de formatage.

        Args:
            document_id: Identifiant du document
            card_type: Type de carte (optionnel)
            analysis_id: Optionnel - si None, utilise la dernière analyse
        """
        pass

    @abstractmethod
    def find_by_id(self, formatting_id: str) -> dict | None:
        """
        Récupère un formatage par son ID.

        Args:
            formatting_id: Identifiant du formatage

        Returns:
            Dict avec les métadonnées ou None
        """
        pass

    @abstractmethod
    def get_formatted_content(
        self,
        document_id: str,
        card_type: str,
        analysis_id: str | None = None
    ) -> str | None:
        """
        Récupère le contenu du fichier Anki.

        Args:
            document_id: Identifiant du document
            card_type: Type de carte
            analysis_id: Optionnel

        Returns:
            Contenu texte ou None
        """
        pass

    @abstractmethod
    def exists_for_optimization(
        self,
        document_id: str,
        card_type: str | None = None
    ) -> bool:
        """
        Vérifie si un formatage existe.

        Args:
            document_id: Identifiant du document
            card_type: Type de carte (optionnel)
        """
        pass

    @abstractmethod
    def find_all(self, document_id: str | None = None) -> list[dict]:
        """
        Liste tous les formatages.

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
        Supprime un formatage et son fichier.

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
        Retourne le chemin du fichier Anki.

        Args:
            document_id: Identifiant du document
            card_type: Type de carte
            analysis_id: Optionnel
        """
        pass
