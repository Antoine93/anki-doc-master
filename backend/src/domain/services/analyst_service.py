"""
Service Analyste du domaine.

Analyse un document PDF pour détecter les modules de contenu présents.
Retourne une liste simple de modules à invoquer pour le restructurateur.

PRINCIPE: Le service orchestre, les adapters implémentent.
- Prompts récupérés via PromptRepositoryPort
- Communication IA via AIPort
"""
import json
import uuid
from datetime import datetime
from typing import Optional, Any

from src.domain.entities.analysis import Analysis
from src.domain.entities.content_module import ContentModule
from src.domain.exceptions import (
    DocumentNotFoundError,
    AnalysisNotFoundError,
    AnalysisAlreadyExistsError,
    DomainValidationError,
    AIError
)
from src.ports.primary.analyze_document_use_case import AnalyzeDocumentUseCase
from src.ports.secondary.document_repository_port import DocumentRepositoryPort
from src.ports.secondary.analysis_storage_port import AnalysisStoragePort
from src.ports.secondary.prompt_repository_port import PromptRepositoryPort
from src.ports.secondary.ai_port import AIPort
from src.infrastructure.logging.config import get_logger

logger = get_logger(__name__, "service")


class AnalystService(AnalyzeDocumentUseCase):
    """
    Service métier pour l'analyse de documents.

    RESPONSABILITÉ: Orchestrer la détection des modules de contenu.

    DÉPENDANCES:
    - DocumentRepositoryPort: Accès aux documents
    - AnalysisStoragePort: Persistance des analyses
    - PromptRepositoryPort: Récupération des prompts
    - AIPort: Communication avec le LLM
    """

    SPECIALIST_ID = "analyst"

    def __init__(
        self,
        document_repository: DocumentRepositoryPort,
        analysis_storage: AnalysisStoragePort,
        prompt_repository: PromptRepositoryPort,
        ai: AIPort
    ) -> None:
        """
        Injection des dépendances.

        Args:
            document_repository: Port pour accéder aux documents
            analysis_storage: Port pour persister les analyses
            prompt_repository: Port pour récupérer les prompts
            ai: Port pour communiquer avec le LLM
        """
        self._document_repo = document_repository
        self._analysis_storage = analysis_storage
        self._prompt_repo = prompt_repository
        self._ai = ai

    def list_documents(self) -> list[dict]:
        """Liste tous les documents avec leur statut d'analyse."""
        logger.debug("Récupération de la liste des documents")
        documents = self._document_repo.find_all()

        for doc in documents:
            doc["has_analysis"] = self._analysis_storage.exists_for_document(doc["id"])

        logger.with_extra(count=len(documents)).info("Documents listés")
        return documents

    def get_document(self, document_id: str) -> dict:
        """Récupère les détails d'un document."""
        self._validate_id(document_id, "document_id")

        logger.with_extra(document_id=document_id).debug("Récupération document")
        doc_dict = self._document_repo.find_by_id(document_id)

        if doc_dict is None:
            logger.with_extra(document_id=document_id).warning("Document introuvable")
            raise DocumentNotFoundError(f"Document avec ID {document_id} introuvable")

        doc_dict["has_analysis"] = self._analysis_storage.exists_for_document(document_id)
        return doc_dict

    def analyze_document(
        self,
        document_id: str,
        force: bool = False
    ) -> dict:
        """
        Lance l'analyse d'un document.

        Workflow:
        1. Récupérer le prompt via PromptRepositoryPort
        2. Envoyer au LLM via AIPort
        3. Parser la réponse JSON
        4. Créer et valider l'entité Analysis
        5. Sauvegarder via AnalysisStoragePort

        Args:
            document_id: L'identifiant du document à analyser
            force: Si True, remplace l'analyse existante

        Returns:
            Dict contenant l'analyse avec modules détectés

        Raises:
            DocumentNotFoundError: Si le document n'existe pas
            AnalysisAlreadyExistsError: Si une analyse existe et force=False
            DomainValidationError: Si les données sont invalides
            AIError: Si la communication avec l'IA échoue
        """
        self._validate_id(document_id, "document_id")

        logger.with_extra(document_id=document_id, force=force).info(
            "Démarrage analyse document"
        )

        # Vérifier que le document existe
        doc_dict = self._document_repo.find_by_id(document_id)
        if doc_dict is None:
            logger.with_extra(document_id=document_id).warning("Document introuvable")
            raise DocumentNotFoundError(f"Document avec ID {document_id} introuvable")

        # Vérifier si une analyse existe déjà
        if not force and self._analysis_storage.exists_for_document(document_id):
            logger.with_extra(document_id=document_id).warning(
                "Analyse existante, force=False"
            )
            raise AnalysisAlreadyExistsError(
                f"Une analyse existe déjà pour le document {document_id}. "
                "Utilisez force=True pour la remplacer."
            )

        # 1. Récupérer le prompt système du spécialiste
        logger.debug("Récupération du prompt analyste")
        prompt = self._prompt_repo.get_system_prompt(self.SPECIALIST_ID)

        # 2. Envoyer au LLM
        logger.debug("Envoi au LLM pour analyse")
        raw_response = self._ai.send_message_with_pdf(
            pdf_path=doc_dict["path"],
            user_message=f"Analyse le document: {doc_dict['name']}",
            system_prompt=prompt
        )

        # 3. Parser la réponse JSON
        logger.debug(f"Réponse LLM reçue ({len(raw_response)} chars)")
        detected_modules = self._parse_detected_modules(raw_response)

        # 4. Filtrer les modules valides
        available_modules = ContentModule.all_modules()
        valid_modules = [m for m in detected_modules if m in available_modules]

        logger.with_extra(
            detected=len(detected_modules),
            valid=len(valid_modules)
        ).debug("Modules validés")

        # 5. Créer l'entité Analysis (validation métier automatique)
        analysis_id = str(uuid.uuid4())[:12]
        try:
            analysis = Analysis(
                analysis_id=analysis_id,
                document_id=document_id,
                detected_modules=valid_modules,
                analyzed_at=datetime.now()
            )
        except ValueError as e:
            logger.error(f"Validation entité Analysis échouée: {e}")
            raise DomainValidationError(str(e))

        # 6. Sauvegarder
        analysis_dict = analysis.to_dict()
        self._analysis_storage.save(analysis_dict)

        logger.with_extra(
            analysis_id=analysis_id,
            module_count=analysis.module_count
        ).info("Analyse complétée et sauvegardée")

        return analysis_dict

    def get_analysis(self, analysis_id: str) -> dict:
        """Récupère les résultats d'une analyse."""
        self._validate_id(analysis_id, "analysis_id")

        logger.with_extra(analysis_id=analysis_id).debug("Récupération analyse")
        analysis_dict = self._analysis_storage.find_by_id(analysis_id)

        if analysis_dict is None:
            logger.with_extra(analysis_id=analysis_id).warning("Analyse introuvable")
            raise AnalysisNotFoundError(f"Analyse avec ID {analysis_id} introuvable")

        return analysis_dict

    def get_analysis_by_document(self, document_id: str) -> Optional[dict]:
        """Récupère l'analyse d'un document spécifique."""
        self._validate_id(document_id, "document_id")

        logger.with_extra(document_id=document_id).debug(
            "Récupération analyse par document"
        )
        return self._analysis_storage.find_by_document_id(document_id)

    def list_analyses(self) -> list[dict]:
        """Liste toutes les analyses existantes."""
        logger.debug("Récupération liste des analyses")
        analyses = self._analysis_storage.find_all()
        logger.with_extra(count=len(analyses)).info("Analyses listées")
        return analyses

    def get_available_modules(self) -> list[dict]:
        """Retourne la liste des modules disponibles pour l'UI."""
        logger.debug("Récupération modules disponibles")
        return [
            {
                "id": module.value,
                "description": ContentModule.get_description(module.value)
            }
            for module in ContentModule
        ]

    def delete_analysis(self, analysis_id: str) -> bool:
        """Supprime une analyse existante."""
        self._validate_id(analysis_id, "analysis_id")

        logger.with_extra(analysis_id=analysis_id).info("Suppression analyse demandée")

        analysis_dict = self._analysis_storage.find_by_id(analysis_id)
        if analysis_dict is None:
            logger.with_extra(analysis_id=analysis_id).warning("Analyse introuvable")
            raise AnalysisNotFoundError(f"Analyse avec ID {analysis_id} introuvable")

        result = self._analysis_storage.delete(analysis_id)
        logger.with_extra(analysis_id=analysis_id, success=result).info(
            "Analyse supprimée"
        )
        return result

    # ==================== Méthodes privées ====================

    def _validate_id(self, value: str, field_name: str) -> None:
        """Valide qu'un identifiant est non vide."""
        if not value or not isinstance(value, str) or value.strip() == "":
            raise DomainValidationError(
                f"Le {field_name} ne peut pas être vide ou invalide"
            )

    def _parse_detected_modules(self, response: str) -> list[str]:
        """
        Parse la réponse JSON du LLM pour extraire les modules détectés.

        Args:
            response: Réponse brute du LLM

        Returns:
            Liste des modules détectés

        Raises:
            AIError: Si le parsing échoue
        """
        response = response.strip()

        if not response:
            raise AIError("Réponse vide du LLM")

        # Extraire JSON des blocs de code markdown
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

        # Parser directement
        try:
            parsed = json.loads(response)
            return parsed.get("detected_modules", [])
        except json.JSONDecodeError:
            pass

        # Chercher JSON dans la réponse
        start = response.find("{")
        end = response.rfind("}") + 1

        if start != -1 and end > start:
            try:
                parsed = json.loads(response[start:end])
                return parsed.get("detected_modules", [])
            except json.JSONDecodeError:
                pass

        logger.error(f"JSON invalide. Réponse: {response[:500]}")
        raise AIError("Réponse LLM invalide - impossible de parser le JSON")

    def _dict_to_entity(self, analysis_dict: dict[str, Any]) -> Analysis:
        """Convertit un dict (repository) en entité Analysis."""
        try:
            analyzed_at = analysis_dict["analyzed_at"]
            if isinstance(analyzed_at, str):
                analyzed_at = datetime.fromisoformat(analyzed_at)

            return Analysis(
                analysis_id=analysis_dict["analysis_id"],
                document_id=analysis_dict["document_id"],
                detected_modules=analysis_dict.get("detected_modules", []),
                analyzed_at=analyzed_at
            )
        except (KeyError, ValueError, TypeError) as e:
            raise DomainValidationError(f"Données d'analyse invalides: {e}")
