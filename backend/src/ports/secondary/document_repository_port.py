"""
Port secondaire pour l'accès aux documents sources.

Interface définissant le contrat pour la lecture des documents PDF
depuis le système de fichiers (dossier sources/).
"""
from abc import ABC, abstractmethod
from typing import Optional


class DocumentRepositoryPort(ABC):
    """
    Interface du repository pour les documents sources.

    RÈGLE: Utilise uniquement des types primitifs (dict, str, int).

    Chaque document a :
    - id: UUID unique (12 caractères)
    - relative_id: Chemin relatif sans extension (ex: "biologie/cellule")

    Structure outputs: outputs/{id}/{analysis_id}/
    Index: outputs/documents_index.json
    """

    @abstractmethod
    def find_all(self) -> list[dict]:
        """
        Liste tous les documents PDF dans le dossier sources/.

        Returns:
            Liste de dicts contenant les métadonnées des documents:
            - id: UUID unique (12 caractères)
            - relative_id: Chemin relatif sans extension
            - name: Nom du fichier sans extension
            - filename: Nom complet avec extension
            - path: Chemin absolu
            - relative_path: Chemin relatif depuis sources/
            - size_bytes: Taille en octets
            - created_at: Date de création (ISO format)
        """
        pass

    @abstractmethod
    def find_by_id(self, document_id: str) -> Optional[dict]:
        """
        Récupère un document par son UUID.

        Args:
            document_id: UUID unique du document (12 caractères)

        Returns:
            Dict contenant les métadonnées ou None si introuvable
        """
        pass

    @abstractmethod
    def find_by_relative_id(self, relative_id: str) -> Optional[dict]:
        """
        Récupère un document par son chemin relatif sans extension.

        Args:
            relative_id: Chemin relatif sans extension (ex: "biologie/cellule")

        Returns:
            Dict contenant les métadonnées ou None si introuvable
        """
        pass

    @abstractmethod
    def find_by_path(self, relative_path: str) -> Optional[dict]:
        """
        Récupère un document par son chemin relatif complet.

        Args:
            relative_path: Chemin relatif depuis sources/ (ex: "biologie/cellule.pdf")

        Returns:
            Dict contenant les métadonnées ou None si introuvable
        """
        pass

    @abstractmethod
    def get_content(self, document_id: str) -> Optional[bytes]:
        """
        Récupère le contenu binaire d'un document.

        Args:
            document_id: Identifiant unique du document

        Returns:
            Contenu binaire du fichier ou None si introuvable
        """
        pass

    @abstractmethod
    def exists(self, document_id: str) -> bool:
        """
        Vérifie si un document existe.

        Args:
            document_id: Identifiant unique du document

        Returns:
            True si le document existe, False sinon
        """
        pass
