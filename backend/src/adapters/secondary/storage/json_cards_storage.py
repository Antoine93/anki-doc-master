"""
Adapter secondaire pour le stockage des cartes générées.

Structure:
    outputs/{document_id}/{analysis_id}/
        ├── cards/
        │   ├── generation-basic.json   # Métadonnées génération basic
        │   ├── generation-cloze.json   # Métadonnées génération cloze
        │   ├── tracking-basic.json     # Tracking basic
        │   ├── tracking-cloze.json     # Tracking cloze
        │   ├── basic/
        │   │   ├── themes/
        │   │   │   ├── card-1.json
        │   │   │   └── card-2.json
        │   │   └── vocabulary/
        │   │       └── card-1.json
        │   └── cloze/
        │       └── themes/
        │           └── card-1.json

Le générateur utilise le même analysis_id que la restructuration.
"""
import json
import shutil
from datetime import datetime
from pathlib import Path

from src.ports.secondary.cards_storage_port import CardsStoragePort


class JsonCardsStorage(CardsStoragePort):
    """
    Implémentation filesystem du stockage des cartes.

    Stocke dans le même dossier que l'analyse/restructuration.
    """

    CARDS_DIR = "cards"
    METADATA_PREFIX = "generation"
    TRACKING_PREFIX = "tracking"
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

    def _get_analysis_path(self, document_id: str, analysis_id: str | None = None) -> Path:
        """Retourne le chemin du dossier d'analyse."""
        document_id = document_id.replace("\\", "/")

        if analysis_id is None:
            analysis_id = self._get_latest_analysis_id(document_id)

        if analysis_id is None:
            raise ValueError(f"Aucune analyse trouvée pour {document_id}")

        return self._outputs_path / document_id / analysis_id

    def _get_cards_path(
        self,
        document_id: str,
        card_type: str,
        analysis_id: str | None = None
    ) -> Path:
        """Retourne le chemin du dossier de cartes."""
        analysis_path = self._get_analysis_path(document_id, analysis_id)
        return analysis_path / self.CARDS_DIR / card_type

    def _get_metadata_filename(self, card_type: str) -> str:
        """Retourne le nom du fichier de métadonnées."""
        return f"{self.METADATA_PREFIX}-{card_type}.json"

    def _get_tracking_filename(self, card_type: str) -> str:
        """Retourne le nom du fichier de tracking."""
        return f"{self.TRACKING_PREFIX}-{card_type}.json"

    def save_generation_metadata(
        self,
        document_id: str,
        card_type: str,
        metadata: dict
    ) -> dict:
        """Sauvegarde les métadonnées dans le dossier cards/."""
        document_id = document_id.replace("\\", "/")

        analysis_id = self._get_latest_analysis_id(document_id)
        if not analysis_id:
            raise ValueError(f"Aucune analyse trouvée pour {document_id}")

        analysis_path = self._outputs_path / document_id / analysis_id
        cards_dir = analysis_path / self.CARDS_DIR
        cards_dir.mkdir(parents=True, exist_ok=True)

        metadata_file = cards_dir / self._get_metadata_filename(card_type)

        metadata["analysis_id"] = analysis_id
        metadata["card_type"] = card_type
        metadata["output_path"] = str(cards_dir / card_type)

        with open(metadata_file, "w", encoding="utf-8") as f:
            json.dump(metadata, f, ensure_ascii=False, indent=2, default=str)

        return metadata

    def save_card(
        self,
        document_id: str,
        card_type: str,
        module: str,
        card_id: str,
        content: dict
    ) -> str:
        """Sauvegarde une carte."""
        cards_path = self._get_cards_path(document_id, card_type)
        module_path = cards_path / module
        module_path.mkdir(parents=True, exist_ok=True)

        card_file = module_path / f"{card_id}.json"

        content["id"] = card_id
        content["module"] = module
        content["card_type"] = card_type

        with open(card_file, "w", encoding="utf-8") as f:
            json.dump(content, f, ensure_ascii=False, indent=2, default=str)

        return str(card_file)

    def get_generation_metadata(
        self,
        document_id: str,
        card_type: str | None = None,
        analysis_id: str | None = None
    ) -> dict | None:
        """Récupère les métadonnées de génération."""
        try:
            analysis_path = self._get_analysis_path(document_id, analysis_id)
        except ValueError:
            return None

        cards_dir = analysis_path / self.CARDS_DIR

        if not cards_dir.exists():
            return None

        # Si card_type spécifié, chercher ce fichier
        if card_type:
            metadata_file = cards_dir / self._get_metadata_filename(card_type)
            if not metadata_file.exists():
                return None
            try:
                with open(metadata_file, "r", encoding="utf-8") as f:
                    return json.load(f)
            except (json.JSONDecodeError, OSError):
                return None

        # Sinon, chercher n'importe quel fichier de génération
        for card_t in ["basic", "cloze"]:
            metadata_file = cards_dir / self._get_metadata_filename(card_t)
            if metadata_file.exists():
                try:
                    with open(metadata_file, "r", encoding="utf-8") as f:
                        return json.load(f)
                except (json.JSONDecodeError, OSError):
                    continue

        return None

    def find_by_id(self, generation_id: str) -> dict | None:
        """Récupère une génération par son ID."""
        for card_type in ["basic", "cloze"]:
            filename = self._get_metadata_filename(card_type)
            for metadata_file in self._outputs_path.rglob(filename):
                try:
                    with open(metadata_file, "r", encoding="utf-8") as f:
                        metadata = json.load(f)
                        if metadata.get("id") == generation_id:
                            return metadata
                except (json.JSONDecodeError, OSError):
                    continue
        return None

    def get_cards(
        self,
        document_id: str,
        card_type: str,
        module: str | None = None,
        analysis_id: str | None = None
    ) -> list[dict]:
        """Récupère les cartes."""
        try:
            cards_path = self._get_cards_path(document_id, card_type, analysis_id)
        except ValueError:
            return []

        if not cards_path.exists():
            return []

        cards = []

        if module:
            # Récupérer les cartes d'un module spécifique
            module_path = cards_path / module
            if module_path.exists():
                for card_file in sorted(module_path.glob("*.json")):
                    try:
                        with open(card_file, "r", encoding="utf-8") as f:
                            cards.append(json.load(f))
                    except (json.JSONDecodeError, OSError):
                        continue
        else:
            # Récupérer toutes les cartes
            for module_dir in cards_path.iterdir():
                if module_dir.is_dir():
                    for card_file in sorted(module_dir.glob("*.json")):
                        try:
                            with open(card_file, "r", encoding="utf-8") as f:
                                cards.append(json.load(f))
                        except (json.JSONDecodeError, OSError):
                            continue

        return cards

    def get_card(
        self,
        document_id: str,
        card_type: str,
        module: str,
        card_id: str,
        analysis_id: str | None = None
    ) -> dict | None:
        """Récupère une carte spécifique."""
        try:
            cards_path = self._get_cards_path(document_id, card_type, analysis_id)
        except ValueError:
            return None

        card_file = cards_path / module / f"{card_id}.json"

        if not card_file.exists():
            return None

        try:
            with open(card_file, "r", encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, OSError):
            return None

    def exists_for_restructuration(
        self,
        document_id: str,
        card_type: str | None = None
    ) -> bool:
        """Vérifie si une génération existe."""
        metadata = self.get_generation_metadata(document_id, card_type)
        return metadata is not None

    def find_all(self, document_id: str | None = None) -> list[dict]:
        """Liste toutes les générations."""
        generations = []

        for card_type in ["basic", "cloze"]:
            filename = self._get_metadata_filename(card_type)

            if document_id:
                # Filtrer par document
                document_id = document_id.replace("\\", "/")
                doc_path = self._outputs_path / document_id
                for metadata_file in doc_path.rglob(filename):
                    try:
                        with open(metadata_file, "r", encoding="utf-8") as f:
                            generations.append(json.load(f))
                    except (json.JSONDecodeError, OSError):
                        continue
            else:
                # Tous les documents
                for metadata_file in self._outputs_path.rglob(filename):
                    try:
                        with open(metadata_file, "r", encoding="utf-8") as f:
                            generations.append(json.load(f))
                    except (json.JSONDecodeError, OSError):
                        continue

        return generations

    def delete(
        self,
        document_id: str,
        card_type: str | None = None,
        analysis_id: str | None = None
    ) -> bool:
        """Supprime une génération et ses cartes."""
        try:
            analysis_path = self._get_analysis_path(document_id, analysis_id)
        except ValueError:
            return False

        cards_dir = analysis_path / self.CARDS_DIR

        if not cards_dir.exists():
            return False

        if card_type:
            # Supprimer uniquement ce type
            metadata_file = cards_dir / self._get_metadata_filename(card_type)
            tracking_file = cards_dir / self._get_tracking_filename(card_type)
            type_dir = cards_dir / card_type

            if metadata_file.exists():
                metadata_file.unlink()
            if tracking_file.exists():
                tracking_file.unlink()
            if type_dir.exists():
                shutil.rmtree(type_dir)
        else:
            # Supprimer tout le dossier cards
            shutil.rmtree(cards_dir)

        return True

    def get_output_path(
        self,
        document_id: str,
        card_type: str,
        analysis_id: str | None = None
    ) -> str:
        """Retourne le chemin du dossier de cartes."""
        try:
            return str(self._get_cards_path(document_id, card_type, analysis_id))
        except ValueError:
            document_id = document_id.replace("\\", "/")
            return str(self._outputs_path / document_id / self.CARDS_DIR / card_type)

    # --- Méthodes de tracking pour reprise ---

    def get_tracking(
        self,
        document_id: str,
        card_type: str,
        analysis_id: str | None = None
    ) -> dict | None:
        """Récupère le fichier de tracking."""
        try:
            analysis_path = self._get_analysis_path(document_id, analysis_id)
        except ValueError:
            return None

        tracking_file = analysis_path / self.CARDS_DIR / self._get_tracking_filename(card_type)

        if not tracking_file.exists():
            return None

        try:
            with open(tracking_file, "r", encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, OSError):
            return None

    def save_tracking(
        self,
        document_id: str,
        card_type: str,
        tracking_data: dict
    ) -> dict:
        """Sauvegarde le fichier de tracking."""
        analysis_path = self._get_analysis_path(document_id)
        cards_dir = analysis_path / self.CARDS_DIR
        cards_dir.mkdir(parents=True, exist_ok=True)

        tracking_file = cards_dir / self._get_tracking_filename(card_type)

        with open(tracking_file, "w", encoding="utf-8") as f:
            json.dump(tracking_data, f, ensure_ascii=False, indent=2, default=str)

        return tracking_data

    def update_module_status(
        self,
        document_id: str,
        card_type: str,
        module: str,
        status: str,
        cards_count: int = 0,
        error: str | None = None
    ) -> dict:
        """Met à jour le statut d'un module dans le tracking."""
        tracking = self.get_tracking(document_id, card_type)
        if tracking is None:
            tracking = self._create_empty_tracking(document_id, card_type)

        now = datetime.now().isoformat()
        tracking["updated_at"] = now

        if module not in tracking["modules"]:
            tracking["modules"][module] = {
                "status": "pending",
                "cards_count": 0,
                "started_at": None,
                "completed_at": None,
                "error": None
            }

        module_data = tracking["modules"][module]
        module_data["status"] = status
        module_data["cards_count"] = cards_count
        module_data["error"] = error

        if status == "in_progress" and module_data["started_at"] is None:
            module_data["started_at"] = now
        elif status in ("completed", "failed"):
            module_data["completed_at"] = now

        # Mettre à jour le statut global
        self._update_global_status(tracking)

        return self.save_tracking(document_id, card_type, tracking)

    def _create_empty_tracking(self, document_id: str, card_type: str) -> dict:
        """Crée une structure de tracking vide."""
        analysis_id = self._get_latest_analysis_id(document_id)
        now = datetime.now().isoformat()

        return {
            "analysis_id": analysis_id,
            "document_id": document_id,
            "card_type": card_type,
            "specialist": "generator",
            "started_at": now,
            "updated_at": now,
            "status": "pending",
            "session_id": None,
            "modules": {}
        }

    def update_session_id(
        self,
        document_id: str,
        card_type: str,
        session_id: str
    ) -> dict:
        """Met à jour le session_id dans le tracking."""
        tracking = self.get_tracking(document_id, card_type)
        if tracking is None:
            tracking = self._create_empty_tracking(document_id, card_type)

        tracking["session_id"] = session_id
        tracking["updated_at"] = datetime.now().isoformat()

        return self.save_tracking(document_id, card_type, tracking)

    def _update_global_status(self, tracking: dict) -> None:
        """Met à jour le statut global basé sur les statuts des modules."""
        modules = tracking.get("modules", {})

        if not modules:
            tracking["status"] = "pending"
            return

        statuses = [m["status"] for m in modules.values()]

        if all(s == "completed" for s in statuses):
            tracking["status"] = "completed"
        elif any(s == "failed" for s in statuses):
            tracking["status"] = "failed"
        elif any(s == "in_progress" for s in statuses):
            tracking["status"] = "in_progress"
        elif any(s == "completed" for s in statuses):
            tracking["status"] = "in_progress"  # Partiellement complété
        else:
            tracking["status"] = "pending"
