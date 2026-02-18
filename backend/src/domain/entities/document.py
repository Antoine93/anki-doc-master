"""
Entité Document représentant un fichier PDF source.

Le document est la source d'entrée du pipeline. Il est localisé
dans le dossier sources/ avec possibilité de sous-dossiers.
"""
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path


@dataclass
class Document:
    """
    Entité représentant un document PDF source.

    Règles métier:
    - Le chemin doit pointer vers un fichier existant
    - L'extension doit être .pdf (pour l'instant)
    - Le nom ne peut pas être vide
    """
    id: str | None
    name: str
    path: str
    size_bytes: int
    created_at: datetime

    def __post_init__(self) -> None:
        """Validation automatique à la création."""
        self._validate()

    def _validate(self) -> None:
        """Valide les règles métier du document."""
        if not self.name or self.name.strip() == "":
            raise ValueError("Le nom du document ne peut pas être vide")

        if not self.path or self.path.strip() == "":
            raise ValueError("Le chemin du document ne peut pas être vide")

        path = Path(self.path)
        if path.suffix.lower() != ".pdf":
            raise ValueError(f"Extension non supportée: {path.suffix}. Seul .pdf est accepté")

        if self.size_bytes < 0:
            raise ValueError("La taille du document ne peut pas être négative")

    @property
    def relative_path(self) -> str:
        """Retourne le chemin relatif depuis le dossier sources/."""
        path = Path(self.path)
        try:
            # Cherche 'sources' dans le chemin et retourne le reste
            parts = path.parts
            if "sources" in parts:
                idx = parts.index("sources")
                return str(Path(*parts[idx + 1:]))
            return path.name
        except (ValueError, IndexError):
            return path.name

    @property
    def extension(self) -> str:
        """Retourne l'extension du fichier."""
        return Path(self.path).suffix.lower()

    def is_valid_pdf(self) -> bool:
        """Vérifie si le fichier est un PDF valide (extension)."""
        return self.extension == ".pdf"
