"""
Adapter secondaire pour le stockage des analyses en JSON.

Structure:
    outputs/{document_id}/{analysis_id}/modules.json

Exemple:
    sources/biologie/cellule.pdf
    → outputs/biologie/cellule/
        ├── a1b2c3d4e5f6/          ← Analyse 1
        │   └── modules.json
        ├── x9y8z7w6v5u4/          ← Analyse 2
        │   └── modules.json
        └── latest.json            ← Référence à la dernière analyse

L'analysis_id est l'identifiant unique de chaque analyse.
Il sert à la fois d'identifiant métier et de nom de dossier.
"""
import json
from pathlib import Path
from typing import Optional

from src.ports.secondary.analysis_storage_port import AnalysisStoragePort


class JsonFileAnalysisStorage(AnalysisStoragePort):
    """
    Implémentation filesystem du storage d'analyses.

    Chaque analyse a son propre dossier identifié par analysis_id.
    Le fichier latest.json pointe vers la dernière analyse.
    """

    ANALYSIS_FILENAME = "modules.json"
    LATEST_FILENAME = "latest.json"

    def __init__(self, outputs_path: str) -> None:
        """Initialise le storage."""
        self._outputs_path = Path(outputs_path)
        self._outputs_path.mkdir(parents=True, exist_ok=True)

    def save(self, analysis_data: dict) -> dict:
        """
        Sauvegarde un résultat d'analyse en JSON.

        Crée un dossier {analysis_id} pour chaque analyse.
        L'analysis_id doit être fourni dans analysis_data par le service.
        """
        document_id = analysis_data.get("document_id")
        if not document_id:
            raise ValueError("document_id requis")

        analysis_id = analysis_data.get("analysis_id")
        if not analysis_id:
            raise ValueError("analysis_id requis")

        document_id = document_id.replace("\\", "/")

        # Créer le dossier: outputs/{document_id}/{analysis_id}/
        analysis_folder = self._outputs_path / document_id / analysis_id
        analysis_folder.mkdir(parents=True, exist_ok=True)

        # Sauvegarder l'analyse
        analysis_file = analysis_folder / self.ANALYSIS_FILENAME
        analysis_data["output_path"] = str(analysis_folder)

        with open(analysis_file, "w", encoding="utf-8") as f:
            json.dump(analysis_data, f, ensure_ascii=False, indent=2, default=str)

        # Mettre à jour latest.json
        self._update_latest(document_id, analysis_id)

        return analysis_data

    def _update_latest(self, document_id: str, analysis_id: str) -> None:
        """Met à jour le pointeur vers la dernière analyse."""
        doc_folder = self._outputs_path / document_id
        latest_file = doc_folder / self.LATEST_FILENAME

        with open(latest_file, "w", encoding="utf-8") as f:
            json.dump({"latest_analysis_id": analysis_id}, f, indent=2)

    def _get_latest_analysis_id(self, document_id: str) -> Optional[str]:
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

    def find_by_id(self, analysis_id: str) -> Optional[dict]:
        """Récupère une analyse par son identifiant unique."""
        for analysis_file in self._outputs_path.rglob(self.ANALYSIS_FILENAME):
            analysis = self._read_json(analysis_file)
            if analysis and analysis.get("analysis_id") == analysis_id:
                return analysis
        return None

    def find_by_analysis_id_and_document(self, document_id: str, analysis_id: str) -> Optional[dict]:
        """Récupère une analyse par document_id et analysis_id (accès direct)."""
        document_id = document_id.replace("\\", "/")
        analysis_file = self._outputs_path / document_id / analysis_id / self.ANALYSIS_FILENAME

        if not analysis_file.exists():
            return None

        return self._read_json(analysis_file)

    def find_by_document_id(self, document_id: str) -> Optional[dict]:
        """Récupère la dernière analyse d'un document."""
        document_id = document_id.replace("\\", "/")
        latest_analysis_id = self._get_latest_analysis_id(document_id)

        if not latest_analysis_id:
            return None

        return self.find_by_analysis_id_and_document(document_id, latest_analysis_id)

    def find_all_for_document(self, document_id: str) -> list[dict]:
        """Liste toutes les analyses d'un document (historique complet)."""
        document_id = document_id.replace("\\", "/")
        doc_folder = self._outputs_path / document_id

        if not doc_folder.exists():
            return []

        analyses = []
        for analysis_folder in doc_folder.iterdir():
            if analysis_folder.is_dir():
                analysis_file = analysis_folder / self.ANALYSIS_FILENAME
                if analysis_file.exists():
                    analysis = self._read_json(analysis_file)
                    if analysis:
                        analyses.append(analysis)

        # Tri par date (plus récent en premier)
        analyses.sort(key=lambda a: a.get("analyzed_at", ""), reverse=True)
        return analyses

    def find_all(self) -> list[dict]:
        """Liste toutes les analyses (derniers runs uniquement)."""
        analyses = []

        # Trouver tous les latest.json
        for latest_file in self._outputs_path.rglob(self.LATEST_FILENAME):
            doc_folder = latest_file.parent
            document_id = str(doc_folder.relative_to(self._outputs_path)).replace("\\", "/")

            analysis = self.find_by_document_id(document_id)
            if analysis:
                analyses.append(analysis)

        analyses.sort(key=lambda a: a.get("analyzed_at", ""), reverse=True)
        return analyses

    def exists_for_document(self, document_id: str) -> bool:
        """Vérifie si au moins une analyse existe pour un document."""
        document_id = document_id.replace("\\", "/")
        latest_file = self._outputs_path / document_id / self.LATEST_FILENAME
        return latest_file.exists()

    def delete(self, analysis_id: str) -> bool:
        """Supprime une analyse spécifique (par son ID)."""
        analysis = self.find_by_id(analysis_id)
        if not analysis:
            return False

        document_id = analysis.get("document_id", "").replace("\\", "/")
        stored_analysis_id = analysis.get("analysis_id")

        if not document_id or not stored_analysis_id:
            return False

        analysis_folder = self._outputs_path / document_id / stored_analysis_id

        try:
            import shutil
            if analysis_folder.exists():
                shutil.rmtree(analysis_folder)

                # Si c'était le latest, mettre à jour
                latest_analysis_id = self._get_latest_analysis_id(document_id)
                if latest_analysis_id == stored_analysis_id:
                    # Trouver l'analyse précédente
                    analyses = self.find_all_for_document(document_id)
                    if analyses:
                        self._update_latest(document_id, analyses[0]["analysis_id"])
                    else:
                        # Plus d'analyses, supprimer latest.json
                        latest_file = self._outputs_path / document_id / self.LATEST_FILENAME
                        latest_file.unlink(missing_ok=True)

                return True
        except OSError:
            pass

        return False

    def _read_json(self, file_path: Path) -> Optional[dict]:
        """Lit un fichier JSON."""
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, OSError):
            return None
