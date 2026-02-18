"""
Adapter secondaire pour la lecture des documents depuis le système de fichiers.

Implémente DocumentRepositoryPort pour scanner le dossier sources/
et récupérer les métadonnées des fichiers PDF.

Chaque document reçoit un UUID unique stocké dans un index.
Structure: outputs/{document_id}/{analysis_id}/
"""
import json
import uuid
from datetime import datetime
from pathlib import Path
from typing import Optional

from src.ports.secondary.document_repository_port import DocumentRepositoryPort


class FileSystemDocumentRepository(DocumentRepositoryPort):
    """
    Implémentation filesystem du repository de documents.

    Scanne le dossier sources/ (avec sous-dossiers) pour trouver
    tous les fichiers PDF disponibles.

    Chaque document a un UUID unique (document_id) stocké dans un index.
    Le chemin relatif est conservé comme 'relative_id' pour référence lisible.

    Index: outputs/documents_index.json
    Structure: {
        "a1b2c3d4e5f6": {
            "relative_path": "6GEI238/Cours1.pdf",
            "registered_at": "2026-02-18T..."
        }
    }
    """

    INDEX_FILENAME = "documents_index.json"

    def __init__(self, sources_path: str, outputs_path: str = None) -> None:
        """
        Initialise le repository.

        Args:
            sources_path: Chemin du dossier sources/
            outputs_path: Chemin du dossier outputs/ (pour l'index)
        """
        self._sources_path = Path(sources_path)
        if not self._sources_path.exists():
            self._sources_path.mkdir(parents=True, exist_ok=True)

        # Dossier outputs pour l'index (par défaut: ../outputs relatif à sources)
        if outputs_path:
            self._outputs_path = Path(outputs_path)
        else:
            self._outputs_path = self._sources_path.parent / "outputs"
        self._outputs_path.mkdir(parents=True, exist_ok=True)

        # Charger ou créer l'index
        self._index_path = self._outputs_path / self.INDEX_FILENAME
        self._index = self._load_index()

    def find_all(self) -> list[dict]:
        """
        Liste tous les documents PDF dans sources/.

        Met à jour l'index avec les nouveaux documents trouvés.
        """
        documents = []
        index_updated = False

        for pdf_path in self._sources_path.rglob("*.pdf"):
            relative_path = str(pdf_path.relative_to(self._sources_path)).replace("\\", "/")

            # Chercher ou créer l'ID pour ce document
            document_id = self._get_id_for_path(relative_path)
            if document_id is None:
                # Nouveau document, générer un UUID
                document_id = str(uuid.uuid4())[:12]
                self._index[document_id] = {
                    "relative_path": relative_path,
                    "registered_at": datetime.now().isoformat()
                }
                index_updated = True

            doc_dict = self._path_to_dict(pdf_path, document_id)
            if doc_dict:
                documents.append(doc_dict)

        # Sauvegarder l'index si mis à jour
        if index_updated:
            self._save_index()

        # Tri par chemin relatif
        documents.sort(key=lambda d: d["relative_id"].lower())
        return documents

    def find_by_id(self, document_id: str) -> Optional[dict]:
        """
        Récupère un document par son identifiant UUID.

        Args:
            document_id: UUID du document (12 caractères)

        Returns:
            Dict avec métadonnées ou None si introuvable
        """
        # Chercher dans l'index
        if document_id not in self._index:
            return None

        relative_path = self._index[document_id]["relative_path"]
        pdf_path = self._sources_path / relative_path

        if not pdf_path.exists():
            return None

        return self._path_to_dict(pdf_path, document_id)

    def find_by_path(self, relative_path: str) -> Optional[dict]:
        """Récupère un document par son chemin relatif complet (avec extension)."""
        relative_path = relative_path.replace("\\", "/")
        full_path = self._sources_path / relative_path

        if not full_path.exists() or full_path.suffix.lower() != ".pdf":
            return None

        # Chercher l'ID pour ce chemin
        document_id = self._get_id_for_path(relative_path)
        if document_id is None:
            # Créer un nouvel ID
            document_id = str(uuid.uuid4())[:12]
            self._index[document_id] = {
                "relative_path": relative_path,
                "registered_at": datetime.now().isoformat()
            }
            self._save_index()

        return self._path_to_dict(full_path, document_id)

    def find_by_relative_id(self, relative_id: str) -> Optional[dict]:
        """
        Récupère un document par son chemin relatif (sans extension).

        Args:
            relative_id: Chemin relatif sans extension (ex: "6GEI238/Cours1")

        Returns:
            Dict avec métadonnées ou None si introuvable
        """
        relative_path = f"{relative_id}.pdf"
        return self.find_by_path(relative_path)

    def get_content(self, document_id: str) -> Optional[bytes]:
        """Récupère le contenu binaire d'un document."""
        doc_dict = self.find_by_id(document_id)
        if doc_dict is None:
            return None

        path = Path(doc_dict["path"])
        if not path.exists():
            return None

        return path.read_bytes()

    def exists(self, document_id: str) -> bool:
        """Vérifie si un document existe."""
        return self.find_by_id(document_id) is not None

    # ==================== Méthodes d'index ====================

    def _load_index(self) -> dict:
        """Charge l'index des documents depuis le fichier JSON."""
        if not self._index_path.exists():
            return {}

        try:
            with open(self._index_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, OSError):
            return {}

    def _save_index(self) -> None:
        """Sauvegarde l'index des documents dans le fichier JSON."""
        with open(self._index_path, "w", encoding="utf-8") as f:
            json.dump(self._index, f, ensure_ascii=False, indent=2)

    def _get_id_for_path(self, relative_path: str) -> Optional[str]:
        """
        Récupère l'ID d'un document par son chemin relatif.

        Args:
            relative_path: Chemin relatif avec extension (ex: "6GEI238/Cours1.pdf")

        Returns:
            UUID du document ou None si non enregistré
        """
        for doc_id, data in self._index.items():
            if data["relative_path"] == relative_path:
                return doc_id
        return None

    def _generate_relative_id(self, path: Path) -> str:
        """
        Génère le relative_id basé sur le chemin relatif sans extension.

        Exemple:
            sources/biologie/cellule.pdf → "biologie/cellule"
        """
        relative = path.relative_to(self._sources_path)
        return str(relative.with_suffix("")).replace("\\", "/")

    def _path_to_dict(self, path: Path, document_id: str) -> Optional[dict]:
        """
        Convertit un chemin en dictionnaire de métadonnées.

        Args:
            path: Chemin absolu du fichier PDF
            document_id: UUID du document

        Returns:
            Dict avec toutes les métadonnées
        """
        try:
            stat = path.stat()
            relative_path = str(path.relative_to(self._sources_path)).replace("\\", "/")

            return {
                "id": document_id,
                "relative_id": self._generate_relative_id(path),
                "name": path.stem,  # Nom sans extension
                "filename": path.name,  # Nom complet avec extension
                "path": str(path),
                "relative_path": relative_path,
                "size_bytes": stat.st_size,
                "created_at": datetime.fromtimestamp(stat.st_ctime).isoformat()
            }
        except (OSError, ValueError):
            return None
