"""
Service Restructurateur du domaine.

Restructure un document PDF en JSON séparés par module.
Utilise le même analysis_id que l'analyse pour stocker dans le même dossier.

PRINCIPE: Le service orchestre, les adapters implémentent.
- Prompts récupérés via PromptRepositoryPort
- Communication IA via AIPort
"""
import json
import uuid
from datetime import datetime

from src.domain.entities.content_module import ContentModule
from src.domain.exceptions import (
    DocumentNotFoundError,
    AIError,
    DomainValidationError,
    RestructurationNotFoundError,
    RestructurationAlreadyExistsError,
    ModuleNotFoundError,
    ItemNotFoundError,
    AnalysisNotFoundError
)
from src.ports.primary.restructure_document_use_case import RestructureDocumentUseCase
from src.ports.secondary.document_repository_port import DocumentRepositoryPort
from src.ports.secondary.restructured_storage_port import RestructuredStoragePort
from src.ports.secondary.prompt_repository_port import PromptRepositoryPort
from src.ports.secondary.ai_port import AIPort
from src.ports.secondary.analysis_storage_port import AnalysisStoragePort
from src.infrastructure.logging.config import get_logger

logger = get_logger(__name__, "service")


class RestructurerService(RestructureDocumentUseCase):
    """
    Service métier pour la restructuration de documents.

    RESPONSABILITÉ: Orchestrer l'extraction de contenu par module.

    DÉPENDANCES:
    - DocumentRepositoryPort: Accès aux documents
    - RestructuredStoragePort: Persistance du contenu restructuré
    - PromptRepositoryPort: Récupération des prompts
    - AIPort: Communication avec le LLM
    """

    SPECIALIST_ID = "restructurer"

    def __init__(
        self,
        document_repository: DocumentRepositoryPort,
        restructured_storage: RestructuredStoragePort,
        prompt_repository: PromptRepositoryPort,
        ai: AIPort,
        analysis_storage: AnalysisStoragePort
    ) -> None:
        """
        Injection des dépendances.

        Args:
            document_repository: Port pour accéder aux documents
            restructured_storage: Port pour persister le contenu restructuré
            prompt_repository: Port pour récupérer les prompts
            ai: Port pour communiquer avec le LLM
            analysis_storage: Port pour accéder aux analyses
        """
        self._document_repo = document_repository
        self._storage = restructured_storage
        self._prompt_repo = prompt_repository
        self._ai = ai
        self._analysis_storage = analysis_storage

    def restructure_document(
        self,
        analysis_id: str,
        force: bool = False
    ) -> dict:
        """
        Restructure un document à partir d'une analyse existante.

        Workflow:
        1. Récupérer l'analyse et extraire document_id + detected_modules
        2. Valider le document et les modules
        3. Vérifier le tracking pour reprise après interruption
        4. Récupérer les prompts via PromptRepositoryPort (lazy loading)
        5. Extraire le contenu via AIPort
        6. Parser et sauvegarder avec tracking

        Args:
            analysis_id: Identifiant de l'analyse
            force: Forcer la re-restructuration (ignore le tracking)

        Returns:
            Dict avec métadonnées de la restructuration

        Raises:
            AnalysisNotFoundError: Analyse inexistante
            DocumentNotFoundError: Document inexistant
            DomainValidationError: Aucun module détecté
            RestructurationAlreadyExistsError: Déjà restructuré
            AIError: Erreur IA
        """
        self._validate_id(analysis_id, "analysis_id")

        logger.with_extra(
            analysis_id=analysis_id,
            force=force
        ).info("Démarrage restructuration depuis analyse")

        # Récupérer l'analyse
        analysis = self._analysis_storage.find_by_id(analysis_id)
        if analysis is None:
            logger.with_extra(analysis_id=analysis_id).warning("Analyse introuvable")
            raise AnalysisNotFoundError(f"Analyse {analysis_id} introuvable")

        # Extraire les infos de l'analyse
        document_id = analysis["document_id"]
        detected_modules = analysis.get("detected_modules", [])

        logger.with_extra(
            document_id=document_id,
            detected_modules=detected_modules
        ).debug("Infos extraites de l'analyse")

        # Valider que des modules ont été détectés
        if not detected_modules:
            raise DomainValidationError("Aucun module détecté dans l'analyse")

        # Filtrer les modules valides
        valid_modules = ContentModule.all_modules()
        selected_modules = [m for m in detected_modules if m in valid_modules]

        if not selected_modules:
            raise DomainValidationError("Aucun module valide dans l'analyse")

        logger.with_extra(
            document_id=document_id,
            modules=selected_modules
        ).info("Modules sélectionnés pour restructuration")

        # Vérifier que le document existe
        doc_dict = self._document_repo.find_by_id(document_id)
        if doc_dict is None:
            logger.with_extra(document_id=document_id).warning("Document introuvable")
            raise DocumentNotFoundError(f"Document {document_id} introuvable")

        # Récupérer ou créer le tracking
        tracking = self._storage.get_tracking(document_id)

        if tracking and not force:
            # Filtrer les modules déjà complétés
            completed_modules = [
                m for m, data in tracking.get("modules", {}).items()
                if data.get("status") == "completed"
            ]
            modules_to_process = [m for m in selected_modules if m not in completed_modules]

            if not modules_to_process:
                logger.info("Tous les modules sont déjà traités")
                return self._storage.get_restructuration_metadata(document_id)

            logger.with_extra(
                skipped=completed_modules,
                remaining=modules_to_process
            ).info("Reprise après interruption")

            selected_modules = modules_to_process
        else:
            # Vérifier si déjà restructuré (sans tracking = ancien comportement)
            if not force and self._storage.exists_for_document(document_id):
                existing = self._storage.get_restructuration_metadata(document_id)
                if existing:
                    logger.with_extra(document_id=document_id).warning(
                        "Restructuration existante"
                    )
                    raise RestructurationAlreadyExistsError(
                        f"Document {document_id} déjà restructuré. Utilisez force=True."
                    )

            # Supprimer l'ancienne si force
            if force:
                self._storage.delete(document_id)

            # Initialiser le tracking
            tracking = self._init_tracking(document_id, analysis_id, selected_modules)
            self._storage.save_tracking(document_id, tracking)

        # Récupérer le prompt système
        logger.debug("Récupération du prompt système")
        system_prompt = self._prompt_repo.get_system_prompt(self.SPECIALIST_ID)

        # Restructurer chaque module
        modules_processed = []
        items_count = {}

        for module in selected_modules:
            logger.with_extra(module=module).debug("Traitement du module")

            # Marquer le module en cours
            self._storage.update_module_status(document_id, module, "in_progress")

            try:
                items = self._extract_module_content(
                    document_path=doc_dict["path"],
                    document_name=doc_dict["name"],
                    module=module,
                    system_prompt=system_prompt
                )

                # Sauvegarder chaque item
                for idx, item in enumerate(items, 1):
                    item_id = f"{module.replace('_', '-')}-{idx}"
                    self._storage.save_module_item(
                        document_id=document_id,
                        module=module,
                        item_id=item_id,
                        content=item
                    )

                # Marquer le module comme terminé
                self._storage.update_module_status(
                    document_id, module, "completed", items_count=len(items)
                )

                modules_processed.append(module)
                items_count[module] = len(items)

                logger.with_extra(
                    module=module,
                    items=len(items)
                ).info("Module traité")

            except AIError as e:
                # Marquer le module comme échoué
                self._storage.update_module_status(
                    document_id, module, "failed", error=str(e)
                )
                logger.with_extra(module=module, error=str(e)).error(
                    "Erreur IA sur module"
                )
                raise  # Interrompt pour permettre la reprise
            except Exception as e:
                # Marquer le module comme échoué
                self._storage.update_module_status(
                    document_id, module, "failed", error=str(e)
                )
                logger.with_extra(module=module, error=str(e)).warning(
                    "Erreur sur module, ignoré"
                )
                continue

        # Sauvegarder les métadonnées
        restructuration_id = str(uuid.uuid4())[:12]
        metadata = {
            "id": restructuration_id,
            "document_id": document_id,
            "document_name": doc_dict["name"],
            "modules_processed": modules_processed,
            "items_count": items_count,
            "restructured_at": datetime.now().isoformat()
        }

        saved = self._storage.save_restructuration_metadata(document_id, metadata)

        logger.with_extra(
            restructuration_id=restructuration_id,
            modules_count=len(modules_processed),
            total_items=sum(items_count.values())
        ).info("Restructuration terminée")

        return saved

    def _init_tracking(
        self,
        document_id: str,
        analysis_id: str,
        modules: list[str]
    ) -> dict:
        """
        Initialise la structure de tracking.

        Args:
            document_id: Identifiant du document
            analysis_id: Identifiant de l'analyse
            modules: Liste des modules à traiter

        Returns:
            Dict avec la structure de tracking initialisée
        """
        now = datetime.now().isoformat()

        tracking = {
            "analysis_id": analysis_id,
            "document_id": document_id,
            "specialist": self.SPECIALIST_ID,
            "started_at": now,
            "updated_at": now,
            "status": "in_progress",
            "modules": {}
        }

        for module in modules:
            tracking["modules"][module] = {
                "status": "pending",
                "items_count": 0,
                "started_at": None,
                "completed_at": None,
                "error": None
            }

        return tracking

    def _extract_module_content(
        self,
        document_path: str,
        document_name: str,
        module: str,
        system_prompt: str
    ) -> list[dict]:
        """
        Extrait le contenu d'un module via l'IA.

        Workflow:
        1. Récupérer le prompt du module via PromptRepositoryPort
        2. Envoyer au LLM via AIPort
        3. Parser la réponse JSON

        Args:
            document_path: Chemin du PDF
            document_name: Nom du document
            module: Identifiant du module
            system_prompt: Prompt système du restructurateur

        Returns:
            Liste des items extraits
        """
        # Récupérer le prompt du module (lazy loaded)
        module_prompt = self._prompt_repo.get_module_prompt(self.SPECIALIST_ID, module)

        # Construire le message utilisateur
        user_message = f"Document: {document_name}\n\n{module_prompt}"

        # LOG: Prompt envoyé
        logger.with_extra(
            module=module,
            system_prompt=system_prompt,
            user_message=user_message
        ).info("Envoi prompt à l'IA")

        # Appeler le LLM
        response = self._ai.send_message_with_pdf(
            pdf_path=document_path,
            user_message=user_message,
            system_prompt=system_prompt
        )

        # LOG: Réponse reçue
        logger.with_extra(
            module=module,
            response=response,
            response_length=len(response)
        ).info("Réponse IA reçue")

        return self._parse_module_items(response, module)

    def _parse_module_items(self, response: str, module: str) -> list[dict]:
        """
        Parse la réponse JSON du LLM pour extraire les items.

        Args:
            response: Réponse brute du LLM
            module: Nom du module (pour le message d'erreur)

        Returns:
            Liste des items

        Raises:
            AIError: Si le parsing échoue
        """
        response = response.strip()

        if not response:
            raise AIError(f"Réponse vide pour module {module}")

        # Extraire JSON des blocs markdown
        if "```json" in response:
            start = response.find("```json") + 7
            end = response.find("```", start)
            if end != -1:
                response = response[start:end].strip()
        elif "```" in response:
            start = response.find("```") + 3
            end = response.find("```", start)
            if end != -1:
                response = response[start:end].strip()

        # Chercher le JSON
        start = response.find("{")
        end = response.rfind("}") + 1
        if start != -1 and end > start:
            response = response[start:end]

        try:
            parsed = json.loads(response)
            return parsed.get("items", [])
        except json.JSONDecodeError as e:
            logger.error(f"JSON invalide pour {module}: {response[:500]}")
            raise AIError(f"JSON invalide pour {module}: {e}")

    def get_restructuration(self, restructuration_id: str) -> dict:
        """Récupère une restructuration par ID."""
        self._validate_id(restructuration_id, "restructuration_id")

        result = self._storage.find_by_id(restructuration_id)
        if result is None:
            raise RestructurationNotFoundError(
                f"Restructuration {restructuration_id} introuvable"
            )
        return result

    def get_restructuration_by_document(self, document_id: str) -> dict | None:
        """Récupère la restructuration d'un document."""
        self._validate_id(document_id, "document_id")
        return self._storage.get_restructuration_metadata(document_id)

    def get_module_content(self, document_id: str, module: str) -> list[dict]:
        """Récupère le contenu d'un module."""
        self._validate_id(document_id, "document_id")

        items = self._storage.get_module_items(document_id, module)
        if not items:
            raise ModuleNotFoundError(
                f"Module {module} introuvable pour {document_id}"
            )
        return items

    def get_module_item(self, document_id: str, module: str, item_id: str) -> dict:
        """Récupère un item spécifique."""
        self._validate_id(document_id, "document_id")

        item = self._storage.get_module_item(document_id, module, item_id)
        if item is None:
            raise ItemNotFoundError(f"Item {item_id} introuvable")
        return item

    def list_restructurations(self) -> list[dict]:
        """Liste toutes les restructurations."""
        logger.debug("Liste des restructurations")
        return self._storage.find_all()

    def delete_restructuration(self, restructuration_id: str) -> bool:
        """Supprime une restructuration."""
        self._validate_id(restructuration_id, "restructuration_id")

        logger.with_extra(restructuration_id=restructuration_id).info(
            "Suppression restructuration"
        )

        result = self._storage.find_by_id(restructuration_id)
        if result is None:
            raise RestructurationNotFoundError(
                f"Restructuration {restructuration_id} introuvable"
            )
        return self._storage.delete(result["document_id"])

    def _validate_id(self, value: str, field_name: str) -> None:
        """Valide qu'un identifiant est non vide."""
        if not value or not isinstance(value, str) or value.strip() == "":
            raise DomainValidationError(
                f"Le {field_name} ne peut pas être vide ou invalide"
            )
