"""
Adapter secondaire pour le stockage du contenu restructuré.

Structure:
    outputs/{document_id}/{analysis_id}/
        ├── modules.json           ← Analyse
        ├── restructuration.json   ← Métadonnées restructuration
        ├── tracking.json          ← Tracking pour reprise
        ├── themes/
        │   ├── theme-1.json
        │   └── theme-2.json
        └── vocabulary/
            └── term-1.json

Le restructurateur utilise le même analysis_id que l'analyse.
"""
import json
import shutil
from datetime import datetime
from pathlib import Path

from src.ports.secondary.restructured_storage_port import RestructuredStoragePort


class JsonRestructuredStorage(RestructuredStoragePort):
    """
    Implémentation filesystem du stockage restructuré.

    Stocke dans le même dossier que l'analyse (identifié par analysis_id).
    """

    METADATA_FILENAME = "restructuration.json"
    LATEST_FILENAME = "latest.json"
    TRACKING_FILENAME = "tracking.json"

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

    def save_restructuration_metadata(
        self,
        document_id: str,
        metadata: dict
    ) -> dict:
        """Sauvegarde les métadonnées dans le dossier de l'analyse actuelle."""
        document_id = document_id.replace("\\", "/")

        # Utiliser l'analysis_id du latest (créé par l'analyse)
        analysis_id = self._get_latest_analysis_id(document_id)
        if not analysis_id:
            raise ValueError(f"Aucune analyse trouvée pour {document_id}")

        analysis_path = self._outputs_path / document_id / analysis_id
        metadata_file = analysis_path / self.METADATA_FILENAME

        metadata["analysis_id"] = analysis_id
        metadata["output_path"] = str(analysis_path)

        with open(metadata_file, "w", encoding="utf-8") as f:
            json.dump(metadata, f, ensure_ascii=False, indent=2, default=str)

        return metadata

    def save_module_item(
        self,
        document_id: str,
        module: str,
        item_id: str,
        content: dict
    ) -> str:
        """Sauvegarde un item de module dans l'analyse courante."""
        analysis_path = self._get_analysis_path(document_id)
        module_path = analysis_path / module
        module_path.mkdir(parents=True, exist_ok=True)

        item_file = module_path / f"{item_id}.json"

        content["id"] = item_id
        content["module"] = module

        with open(item_file, "w", encoding="utf-8") as f:
            json.dump(content, f, ensure_ascii=False, indent=2, default=str)

        return str(item_file)

    def get_restructuration_metadata(self, document_id: str, analysis_id: str | None = None) -> dict | None:
        """Récupère les métadonnées de restructuration."""
        try:
            analysis_path = self._get_analysis_path(document_id, analysis_id)
        except ValueError:
            return None

        metadata_file = analysis_path / self.METADATA_FILENAME

        if not metadata_file.exists():
            return None

        try:
            with open(metadata_file, "r", encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, OSError):
            return None

    def find_by_id(self, restructuration_id: str) -> dict | None:
        """Récupère une restructuration par son ID."""
        for metadata_file in self._outputs_path.rglob(self.METADATA_FILENAME):
            try:
                with open(metadata_file, "r", encoding="utf-8") as f:
                    metadata = json.load(f)
                    if metadata.get("id") == restructuration_id:
                        return metadata
            except (json.JSONDecodeError, OSError):
                continue
        return None

    def get_module_items(self, document_id: str, module: str, analysis_id: str | None = None) -> list[dict]:
        """Récupère tous les items d'un module."""
        try:
            analysis_path = self._get_analysis_path(document_id, analysis_id)
        except ValueError:
            return []

        module_path = analysis_path / module

        if not module_path.exists():
            return []

        items = []
        for item_file in sorted(module_path.glob("*.json")):
            try:
                with open(item_file, "r", encoding="utf-8") as f:
                    items.append(json.load(f))
            except (json.JSONDecodeError, OSError):
                continue

        return items

    def get_module_item(
        self,
        document_id: str,
        module: str,
        item_id: str,
        analysis_id: str | None = None
    ) -> dict | None:
        """Récupère un item spécifique."""
        try:
            analysis_path = self._get_analysis_path(document_id, analysis_id)
        except ValueError:
            return None

        item_file = analysis_path / module / f"{item_id}.json"

        if not item_file.exists():
            return None

        try:
            with open(item_file, "r", encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, OSError):
            return None

    def exists_for_document(self, document_id: str) -> bool:
        """Vérifie si une restructuration existe dans le dernier run."""
        metadata = self.get_restructuration_metadata(document_id)
        return metadata is not None

    def find_all(self) -> list[dict]:
        """Liste toutes les restructurations (derniers runs)."""
        restructurations = []

        for metadata_file in self._outputs_path.rglob(self.METADATA_FILENAME):
            try:
                with open(metadata_file, "r", encoding="utf-8") as f:
                    restructurations.append(json.load(f))
            except (json.JSONDecodeError, OSError):
                continue

        return restructurations

    def delete(self, document_id: str, analysis_id: str | None = None) -> bool:
        """Supprime la restructuration (garde l'analyse)."""
        try:
            analysis_path = self._get_analysis_path(document_id, analysis_id)
        except ValueError:
            return False

        # Supprimer le fichier de métadonnées
        metadata_file = analysis_path / self.METADATA_FILENAME
        if metadata_file.exists():
            metadata_file.unlink()

        # Supprimer les dossiers de modules
        for item in analysis_path.iterdir():
            if item.is_dir():
                shutil.rmtree(item)

        return True

    def get_output_path(self, document_id: str, analysis_id: str | None = None) -> str:
        """Retourne le chemin du dossier d'analyse."""
        try:
            return str(self._get_analysis_path(document_id, analysis_id))
        except ValueError:
            document_id = document_id.replace("\\", "/")
            return str(self._outputs_path / document_id)

    # --- Méthodes de tracking pour reprise ---

    def get_tracking(self, document_id: str, analysis_id: str | None = None) -> dict | None:
        """Récupère le fichier de tracking."""
        try:
            analysis_path = self._get_analysis_path(document_id, analysis_id)
        except ValueError:
            return None

        tracking_file = analysis_path / self.TRACKING_FILENAME

        if not tracking_file.exists():
            return None

        try:
            with open(tracking_file, "r", encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, OSError):
            return None

    def save_tracking(self, document_id: str, tracking_data: dict) -> dict:
        """Sauvegarde le fichier de tracking."""
        analysis_path = self._get_analysis_path(document_id)
        tracking_file = analysis_path / self.TRACKING_FILENAME

        with open(tracking_file, "w", encoding="utf-8") as f:
            json.dump(tracking_data, f, ensure_ascii=False, indent=2, default=str)

        return tracking_data

    def update_module_status(
        self,
        document_id: str,
        module: str,
        status: str,
        items_count: int = 0,
        error: str | None = None
    ) -> dict:
        """Met à jour le statut d'un module dans le tracking."""
        tracking = self.get_tracking(document_id)
        if tracking is None:
            tracking = self._create_empty_tracking(document_id)

        now = datetime.now().isoformat()
        tracking["updated_at"] = now

        if module not in tracking["modules"]:
            tracking["modules"][module] = {
                "status": "pending",
                "items_count": 0,
                "started_at": None,
                "completed_at": None,
                "error": None
            }

        module_data = tracking["modules"][module]
        module_data["status"] = status
        module_data["items_count"] = items_count
        module_data["error"] = error

        if status == "in_progress" and module_data["started_at"] is None:
            module_data["started_at"] = now
        elif status in ("completed", "failed"):
            module_data["completed_at"] = now

        # Mettre à jour le statut global
        self._update_global_status(tracking)

        return self.save_tracking(document_id, tracking)

    def _create_empty_tracking(self, document_id: str) -> dict:
        """Crée une structure de tracking vide."""
        analysis_id = self._get_latest_analysis_id(document_id)
        now = datetime.now().isoformat()

        return {
            "analysis_id": analysis_id,
            "document_id": document_id,
            "specialist": "restructurer",
            "started_at": now,
            "updated_at": now,
            "status": "pending",
            "session_id": None,  # ID session Claude pour reprise
            "modules": {}
        }

    def update_session_id(self, document_id: str, session_id: str) -> dict:
        """
        Met à jour le session_id dans le tracking.

        Args:
            document_id: Identifiant du document
            session_id: ID de session Claude

        Returns:
            Tracking mis à jour
        """
        tracking = self.get_tracking(document_id)
        if tracking is None:
            tracking = self._create_empty_tracking(document_id)

        tracking["session_id"] = session_id
        tracking["updated_at"] = datetime.now().isoformat()

        return self.save_tracking(document_id, tracking)

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
