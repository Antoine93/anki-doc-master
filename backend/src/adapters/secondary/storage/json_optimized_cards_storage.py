"""
Adapter secondaire pour le stockage des cartes optimisées.

Structure:
    outputs/{document_id}/{analysis_id}/
        ├── cards/
        │   ├── basic/                    # Cartes générées
        │   └── optimized/                # Cartes optimisées
        │       ├── optimization-basic.json
        │       ├── tracking-basic.json
        │       └── basic/
        │           ├── themes/
        │           │   ├── card-1.json
        │           │   └── card-2.json
        │           └── vocabulary/
        │               └── card-1.json

L'optimiseur stocke dans cards/optimized/{card_type}/.
"""
import json
import shutil
from datetime import datetime
from pathlib import Path

from src.ports.secondary.optimized_cards_storage_port import OptimizedCardsStoragePort


class JsonOptimizedCardsStorage(OptimizedCardsStoragePort):
    """
    Implémentation filesystem du stockage des cartes optimisées.

    Stocke dans le sous-dossier 'optimized' du dossier cards.
    """

    CARDS_DIR = "cards"
    OPTIMIZED_DIR = "optimized"
    METADATA_PREFIX = "optimization"
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

    def _get_optimized_path(
        self,
        document_id: str,
        card_type: str,
        analysis_id: str | None = None
    ) -> Path:
        """Retourne le chemin du dossier de cartes optimisées."""
        analysis_path = self._get_analysis_path(document_id, analysis_id)
        return analysis_path / self.CARDS_DIR / self.OPTIMIZED_DIR / card_type

    def _get_optimized_base_path(
        self,
        document_id: str,
        analysis_id: str | None = None
    ) -> Path:
        """Retourne le chemin de base du dossier optimized."""
        analysis_path = self._get_analysis_path(document_id, analysis_id)
        return analysis_path / self.CARDS_DIR / self.OPTIMIZED_DIR

    def _get_metadata_filename(self, card_type: str) -> str:
        """Retourne le nom du fichier de métadonnées."""
        return f"{self.METADATA_PREFIX}-{card_type}.json"

    def _get_tracking_filename(self, card_type: str) -> str:
        """Retourne le nom du fichier de tracking."""
        return f"{self.TRACKING_PREFIX}-{card_type}.json"

    def save_optimization_metadata(
        self,
        document_id: str,
        card_type: str,
        metadata: dict
    ) -> dict:
        """Sauvegarde les métadonnées dans le dossier optimized/."""
        document_id = document_id.replace("\\", "/")

        analysis_id = self._get_latest_analysis_id(document_id)
        if not analysis_id:
            raise ValueError(f"Aucune analyse trouvée pour {document_id}")

        optimized_base = self._get_optimized_base_path(document_id, analysis_id)
        optimized_base.mkdir(parents=True, exist_ok=True)

        metadata_file = optimized_base / self._get_metadata_filename(card_type)

        metadata["analysis_id"] = analysis_id
        metadata["card_type"] = card_type
        metadata["output_path"] = str(optimized_base / card_type)

        with open(metadata_file, "w", encoding="utf-8") as f:
            json.dump(metadata, f, ensure_ascii=False, indent=2, default=str)

        return metadata

    def save_optimized_card(
        self,
        document_id: str,
        card_type: str,
        module: str,
        card_id: str,
        content: dict
    ) -> str:
        """Sauvegarde une carte optimisée."""
        optimized_path = self._get_optimized_path(document_id, card_type)
        module_path = optimized_path / module
        module_path.mkdir(parents=True, exist_ok=True)

        card_file = module_path / f"{card_id}.json"

        content["id"] = card_id
        content["module"] = module
        content["card_type"] = card_type
        content["optimized"] = True

        with open(card_file, "w", encoding="utf-8") as f:
            json.dump(content, f, ensure_ascii=False, indent=2, default=str)

        return str(card_file)

    def get_optimization_metadata(
        self,
        document_id: str,
        card_type: str | None = None,
        analysis_id: str | None = None
    ) -> dict | None:
        """Récupère les métadonnées d'optimisation."""
        try:
            optimized_base = self._get_optimized_base_path(document_id, analysis_id)
        except ValueError:
            return None

        if not optimized_base.exists():
            return None

        if card_type:
            metadata_file = optimized_base / self._get_metadata_filename(card_type)
            if not metadata_file.exists():
                return None
            try:
                with open(metadata_file, "r", encoding="utf-8") as f:
                    return json.load(f)
            except (json.JSONDecodeError, OSError):
                return None

        # Sinon, chercher n'importe quel fichier d'optimisation
        for card_t in ["basic", "cloze"]:
            metadata_file = optimized_base / self._get_metadata_filename(card_t)
            if metadata_file.exists():
                try:
                    with open(metadata_file, "r", encoding="utf-8") as f:
                        return json.load(f)
                except (json.JSONDecodeError, OSError):
                    continue

        return None

    def find_by_id(self, optimization_id: str) -> dict | None:
        """Récupère une optimisation par son ID."""
        for card_type in ["basic", "cloze"]:
            filename = self._get_metadata_filename(card_type)
            for metadata_file in self._outputs_path.rglob(f"**/{self.OPTIMIZED_DIR}/{filename}"):
                try:
                    with open(metadata_file, "r", encoding="utf-8") as f:
                        metadata = json.load(f)
                        if metadata.get("id") == optimization_id:
                            return metadata
                except (json.JSONDecodeError, OSError):
                    continue
        return None

    def get_optimized_cards(
        self,
        document_id: str,
        card_type: str,
        module: str | None = None,
        analysis_id: str | None = None
    ) -> list[dict]:
        """Récupère les cartes optimisées."""
        try:
            optimized_path = self._get_optimized_path(document_id, card_type, analysis_id)
        except ValueError:
            return []

        if not optimized_path.exists():
            return []

        cards = []

        if module:
            module_path = optimized_path / module
            if module_path.exists():
                for card_file in sorted(module_path.glob("*.json")):
                    try:
                        with open(card_file, "r", encoding="utf-8") as f:
                            cards.append(json.load(f))
                    except (json.JSONDecodeError, OSError):
                        continue
        else:
            for module_dir in optimized_path.iterdir():
                if module_dir.is_dir():
                    for card_file in sorted(module_dir.glob("*.json")):
                        try:
                            with open(card_file, "r", encoding="utf-8") as f:
                                cards.append(json.load(f))
                        except (json.JSONDecodeError, OSError):
                            continue

        return cards

    def get_optimized_card(
        self,
        document_id: str,
        card_type: str,
        module: str,
        card_id: str,
        analysis_id: str | None = None
    ) -> dict | None:
        """Récupère une carte optimisée spécifique."""
        try:
            optimized_path = self._get_optimized_path(document_id, card_type, analysis_id)
        except ValueError:
            return None

        card_file = optimized_path / module / f"{card_id}.json"

        if not card_file.exists():
            return None

        try:
            with open(card_file, "r", encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, OSError):
            return None

    def exists_for_generation(
        self,
        document_id: str,
        card_type: str | None = None
    ) -> bool:
        """Vérifie si une optimisation existe."""
        metadata = self.get_optimization_metadata(document_id, card_type)
        return metadata is not None

    def find_all(self, document_id: str | None = None) -> list[dict]:
        """Liste toutes les optimisations."""
        optimizations = []

        for card_type in ["basic", "cloze"]:
            filename = self._get_metadata_filename(card_type)
            pattern = f"**/{self.OPTIMIZED_DIR}/{filename}"

            if document_id:
                document_id = document_id.replace("\\", "/")
                doc_path = self._outputs_path / document_id
                search_path = doc_path
            else:
                search_path = self._outputs_path

            for metadata_file in search_path.rglob(pattern):
                try:
                    with open(metadata_file, "r", encoding="utf-8") as f:
                        optimizations.append(json.load(f))
                except (json.JSONDecodeError, OSError):
                    continue

        return optimizations

    def delete(
        self,
        document_id: str,
        card_type: str | None = None,
        analysis_id: str | None = None
    ) -> bool:
        """Supprime une optimisation et ses cartes."""
        try:
            optimized_base = self._get_optimized_base_path(document_id, analysis_id)
        except ValueError:
            return False

        if not optimized_base.exists():
            return False

        if card_type:
            # Supprimer uniquement ce type
            metadata_file = optimized_base / self._get_metadata_filename(card_type)
            tracking_file = optimized_base / self._get_tracking_filename(card_type)
            type_dir = optimized_base / card_type

            if metadata_file.exists():
                metadata_file.unlink()
            if tracking_file.exists():
                tracking_file.unlink()
            if type_dir.exists():
                shutil.rmtree(type_dir)
        else:
            # Supprimer tout le dossier optimized
            shutil.rmtree(optimized_base)

        return True

    def get_output_path(
        self,
        document_id: str,
        card_type: str,
        analysis_id: str | None = None
    ) -> str:
        """Retourne le chemin du dossier de cartes optimisées."""
        try:
            return str(self._get_optimized_path(document_id, card_type, analysis_id))
        except ValueError:
            document_id = document_id.replace("\\", "/")
            return str(
                self._outputs_path / document_id / self.CARDS_DIR /
                self.OPTIMIZED_DIR / card_type
            )

    # --- Méthodes de tracking pour reprise ---

    def get_tracking(
        self,
        document_id: str,
        card_type: str,
        analysis_id: str | None = None
    ) -> dict | None:
        """Récupère le fichier de tracking."""
        try:
            optimized_base = self._get_optimized_base_path(document_id, analysis_id)
        except ValueError:
            return None

        tracking_file = optimized_base / self._get_tracking_filename(card_type)

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
        optimized_base = self._get_optimized_base_path(document_id)
        optimized_base.mkdir(parents=True, exist_ok=True)

        tracking_file = optimized_base / self._get_tracking_filename(card_type)

        with open(tracking_file, "w", encoding="utf-8") as f:
            json.dump(tracking_data, f, ensure_ascii=False, indent=2, default=str)

        return tracking_data

    def update_module_status(
        self,
        document_id: str,
        card_type: str,
        module: str,
        status: str,
        cards_input: int = 0,
        cards_output: int = 0,
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
                "cards_input": 0,
                "cards_output": 0,
                "started_at": None,
                "completed_at": None,
                "error": None
            }

        module_data = tracking["modules"][module]
        module_data["status"] = status
        module_data["cards_input"] = cards_input
        module_data["cards_output"] = cards_output
        module_data["error"] = error

        if status == "in_progress" and module_data["started_at"] is None:
            module_data["started_at"] = now
        elif status in ("completed", "failed"):
            module_data["completed_at"] = now

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
            "specialist": "atomizer",
            "started_at": now,
            "updated_at": now,
            "status": "pending",
            "modules": {}
        }

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
            tracking["status"] = "in_progress"
        else:
            tracking["status"] = "pending"
