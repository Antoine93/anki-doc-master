"""
Adapter secondaire pour le stockage des fichiers Anki formatés.

Structure:
    outputs/{document_id}/{analysis_id}/
        ├── cards/
        │   ├── optimized/            # Cartes optimisées (source)
        │   └── anki/                 # Fichiers Anki exportés
        │       ├── formatting-basic.json
        │       ├── formatting-cloze.json
        │       ├── basic.txt
        │       └── cloze.txt

Le formatter stocke dans cards/anki/.
"""
import json
import shutil
from datetime import datetime
from pathlib import Path

from src.ports.secondary.formatted_cards_storage_port import FormattedCardsStoragePort


class AnkiFormattedStorage(FormattedCardsStoragePort):
    """
    Implémentation filesystem du stockage des fichiers Anki.

    Stocke les fichiers .txt et métadonnées dans cards/anki/.
    """

    CARDS_DIR = "cards"
    ANKI_DIR = "anki"
    METADATA_PREFIX = "formatting"
    LATEST_FILENAME = "latest.json"

    def __init__(self, outputs_path: str) -> None:
        """Initialise le storage."""
        self._outputs_path = Path(outputs_path)
        self._outputs_path.mkdir(parents=True, exist_ok=True)

    def _get_latest_analysis_id(self, document_id: str) -> str | None:
        """Récupère l'ID de la dernière analyse pour un document."""
        document_id = document_id.replace("\\", "/")
        latest_file = self._outputs_path / document_id / self.LATEST_FILENAME

        if not latest_file.exists():
            return None

        try:
            with open(latest_file, "r", encoding="utf-8") as f:
                data = json.load(f)
                return data.get("latest_analysis_id")
        except (json.JSONDecodeError, OSError):
            return None

    def _get_analysis_path(
        self,
        document_id: str,
        analysis_id: str | None = None
    ) -> Path:
        """Retourne le chemin du dossier d'analyse."""
        document_id = document_id.replace("\\", "/")

        if analysis_id is None:
            analysis_id = self._get_latest_analysis_id(document_id)

        if analysis_id is None:
            raise ValueError(f"Aucune analyse trouvée pour {document_id}")

        return self._outputs_path / document_id / analysis_id

    def _get_anki_path(
        self,
        document_id: str,
        analysis_id: str | None = None
    ) -> Path:
        """Retourne le chemin du dossier anki."""
        analysis_path = self._get_analysis_path(document_id, analysis_id)
        return analysis_path / self.CARDS_DIR / self.ANKI_DIR

    def _get_metadata_filename(self, card_type: str) -> str:
        """Retourne le nom du fichier de métadonnées."""
        return f"{self.METADATA_PREFIX}-{card_type}.json"

    def _get_anki_filename(self, card_type: str) -> str:
        """Retourne le nom du fichier Anki .txt."""
        return f"{card_type}.txt"

    def save_formatting_metadata(
        self,
        document_id: str,
        card_type: str,
        metadata: dict
    ) -> dict:
        """Sauvegarde les métadonnées dans le dossier anki/."""
        document_id = document_id.replace("\\", "/")

        analysis_id = self._get_latest_analysis_id(document_id)
        if not analysis_id:
            raise ValueError(f"Aucune analyse trouvée pour {document_id}")

        anki_path = self._get_anki_path(document_id, analysis_id)
        anki_path.mkdir(parents=True, exist_ok=True)

        metadata_file = anki_path / self._get_metadata_filename(card_type)

        metadata["analysis_id"] = analysis_id
        metadata["card_type"] = card_type
        metadata["output_file"] = str(anki_path / self._get_anki_filename(card_type))

        with open(metadata_file, "w", encoding="utf-8") as f:
            json.dump(metadata, f, ensure_ascii=False, indent=2, default=str)

        return metadata

    def save_formatted_file(
        self,
        document_id: str,
        card_type: str,
        content: str
    ) -> str:
        """Sauvegarde le fichier Anki .txt."""
        document_id = document_id.replace("\\", "/")

        anki_path = self._get_anki_path(document_id)
        anki_path.mkdir(parents=True, exist_ok=True)

        anki_file = anki_path / self._get_anki_filename(card_type)

        with open(anki_file, "w", encoding="utf-8") as f:
            f.write(content)

        return str(anki_file)

    def get_formatting_metadata(
        self,
        document_id: str,
        card_type: str | None = None,
        analysis_id: str | None = None
    ) -> dict | None:
        """Récupère les métadonnées de formatage."""
        try:
            anki_path = self._get_anki_path(document_id, analysis_id)
        except ValueError:
            return None

        if not anki_path.exists():
            return None

        if card_type:
            metadata_file = anki_path / self._get_metadata_filename(card_type)
            if not metadata_file.exists():
                return None
            try:
                with open(metadata_file, "r", encoding="utf-8") as f:
                    return json.load(f)
            except (json.JSONDecodeError, OSError):
                return None

        # Sinon, chercher n'importe quel fichier de formatage
        for card_t in ["basic", "cloze"]:
            metadata_file = anki_path / self._get_metadata_filename(card_t)
            if metadata_file.exists():
                try:
                    with open(metadata_file, "r", encoding="utf-8") as f:
                        return json.load(f)
                except (json.JSONDecodeError, OSError):
                    continue

        return None

    def find_by_id(self, formatting_id: str) -> dict | None:
        """Récupère un formatage par son ID."""
        for card_type in ["basic", "cloze"]:
            filename = self._get_metadata_filename(card_type)
            for metadata_file in self._outputs_path.rglob(
                f"**/{self.ANKI_DIR}/{filename}"
            ):
                try:
                    with open(metadata_file, "r", encoding="utf-8") as f:
                        metadata = json.load(f)
                        if metadata.get("id") == formatting_id:
                            return metadata
                except (json.JSONDecodeError, OSError):
                    continue
        return None

    def get_formatted_content(
        self,
        document_id: str,
        card_type: str,
        analysis_id: str | None = None
    ) -> str | None:
        """Récupère le contenu du fichier Anki."""
        try:
            anki_path = self._get_anki_path(document_id, analysis_id)
        except ValueError:
            return None

        anki_file = anki_path / self._get_anki_filename(card_type)

        if not anki_file.exists():
            return None

        try:
            with open(anki_file, "r", encoding="utf-8") as f:
                return f.read()
        except OSError:
            return None

    def exists_for_optimization(
        self,
        document_id: str,
        card_type: str | None = None
    ) -> bool:
        """Vérifie si un formatage existe."""
        metadata = self.get_formatting_metadata(document_id, card_type)
        return metadata is not None

    def find_all(self, document_id: str | None = None) -> list[dict]:
        """Liste tous les formatages."""
        formattings = []

        for card_type in ["basic", "cloze"]:
            filename = self._get_metadata_filename(card_type)
            pattern = f"**/{self.ANKI_DIR}/{filename}"

            if document_id:
                document_id = document_id.replace("\\", "/")
                search_path = self._outputs_path / document_id
            else:
                search_path = self._outputs_path

            for metadata_file in search_path.rglob(pattern):
                try:
                    with open(metadata_file, "r", encoding="utf-8") as f:
                        formattings.append(json.load(f))
                except (json.JSONDecodeError, OSError):
                    continue

        return formattings

    def delete(
        self,
        document_id: str,
        card_type: str | None = None,
        analysis_id: str | None = None
    ) -> bool:
        """Supprime un formatage et son fichier."""
        try:
            anki_path = self._get_anki_path(document_id, analysis_id)
        except ValueError:
            return False

        if not anki_path.exists():
            return False

        if card_type:
            # Supprimer uniquement ce type
            metadata_file = anki_path / self._get_metadata_filename(card_type)
            anki_file = anki_path / self._get_anki_filename(card_type)

            if metadata_file.exists():
                metadata_file.unlink()
            if anki_file.exists():
                anki_file.unlink()
        else:
            # Supprimer tout le dossier anki
            shutil.rmtree(anki_path)

        return True

    def get_output_path(
        self,
        document_id: str,
        card_type: str,
        analysis_id: str | None = None
    ) -> str:
        """Retourne le chemin du fichier Anki."""
        try:
            anki_path = self._get_anki_path(document_id, analysis_id)
            return str(anki_path / self._get_anki_filename(card_type))
        except ValueError:
            document_id = document_id.replace("\\", "/")
            return str(
                self._outputs_path / document_id / self.CARDS_DIR /
                self.ANKI_DIR / self._get_anki_filename(card_type)
            )
