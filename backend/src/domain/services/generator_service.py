"""
Service Générateur de cartes du domaine.

Génère des cartes Anki à partir du contenu restructuré.
Supporte plusieurs types de cartes (basic, cloze).

PRINCIPE: Le service orchestre, les adapters implémentent.
- Prompts récupérés via PromptRepositoryPort
- Communication IA via AIPort
"""
import json
import re
import time
import uuid
from datetime import datetime

from src.domain.exceptions import (
    DomainValidationError,
    AIError,
    RestructurationNotFoundError,
    GenerationNotFoundError,
    GenerationAlreadyExistsError,
    CardNotFoundError
)
from src.ports.primary.generate_cards_use_case import GenerateCardsUseCase
from src.ports.secondary.restructured_storage_port import RestructuredStoragePort
from src.ports.secondary.cards_storage_port import CardsStoragePort
from src.ports.secondary.prompt_repository_port import PromptRepositoryPort
from src.ports.secondary.ai_port import AIPort
from src.infrastructure.logging.config import get_logger

logger = get_logger(__name__, "service")


class GeneratorService(GenerateCardsUseCase):
    """
    Service métier pour la génération de cartes Anki.

    RESPONSABILITÉ: Orchestrer la génération de cartes à partir du contenu restructuré.

    DÉPENDANCES:
    - RestructuredStoragePort: Accès au contenu restructuré
    - CardsStoragePort: Persistance des cartes générées
    - PromptRepositoryPort: Récupération des prompts
    - AIPort: Communication avec le LLM
    """

    SPECIALIST_ID = "generator"
    VALID_CARD_TYPES = ["basic", "cloze"]
    # Modules exclus par défaut (nécessitent traitement spécial des images)
    EXCLUDED_MODULES_DEFAULT = ["images_list", "images_descriptions"]

    def __init__(
        self,
        restructured_storage: RestructuredStoragePort,
        cards_storage: CardsStoragePort,
        prompt_repository: PromptRepositoryPort,
        ai: AIPort
    ) -> None:
        """
        Injection des dépendances.

        Args:
            restructured_storage: Port pour accéder au contenu restructuré
            cards_storage: Port pour persister les cartes
            prompt_repository: Port pour récupérer les prompts
            ai: Port pour communiquer avec le LLM
        """
        self._restructured_storage = restructured_storage
        self._cards_storage = cards_storage
        self._prompt_repo = prompt_repository
        self._ai = ai

    def generate_cards(
        self,
        restructuration_id: str,
        card_type: str = "basic",
        modules: list[str] | None = None,
        force: bool = False
    ) -> dict:
        """
        Génère des cartes Anki à partir d'une restructuration.

        Workflow:
        1. Récupérer la restructuration et extraire les modules
        2. Valider le type de carte
        3. Vérifier le tracking pour reprise après interruption
        4. Récupérer les prompts via PromptRepositoryPort
        5. Générer les cartes via AIPort
        6. Parser et sauvegarder avec tracking

        Args:
            restructuration_id: Identifiant de la restructuration
            card_type: Type de carte (basic, cloze)
            modules: Liste des modules à traiter (None = tous)
            force: Forcer la re-génération

        Returns:
            Dict avec métadonnées de la génération

        Raises:
            RestructurationNotFoundError: Restructuration inexistante
            DomainValidationError: Type de carte invalide
            GenerationAlreadyExistsError: Déjà généré
            AIError: Erreur IA
        """
        self._validate_id(restructuration_id, "restructuration_id")
        self._validate_card_type(card_type)

        logger.with_extra(
            restructuration_id=restructuration_id,
            card_type=card_type,
            modules=modules,
            force=force
        ).info("Démarrage génération de cartes")

        # Récupérer la restructuration
        restructuration = self._restructured_storage.find_by_id(restructuration_id)
        if restructuration is None:
            logger.with_extra(restructuration_id=restructuration_id).warning(
                "Restructuration introuvable"
            )
            raise RestructurationNotFoundError(
                f"Restructuration {restructuration_id} introuvable"
            )

        # Extraire les infos
        document_id = restructuration["document_id"]
        available_modules = restructuration.get("modules_processed", [])

        logger.with_extra(
            document_id=document_id,
            available_modules=available_modules
        ).debug("Infos extraites de la restructuration")

        # Filtrer les modules demandés
        if modules:
            # Modules explicitement demandés: inclure même les exclus par défaut
            selected_modules = [m for m in modules if m in available_modules]
            if not selected_modules:
                raise DomainValidationError(
                    f"Aucun des modules demandés n'est disponible. "
                    f"Disponibles: {available_modules}"
                )
        else:
            # Aucun module spécifié: exclure les modules par défaut (images)
            selected_modules = [
                m for m in available_modules
                if m not in self.EXCLUDED_MODULES_DEFAULT
            ]
            excluded = [m for m in available_modules if m in self.EXCLUDED_MODULES_DEFAULT]
            if excluded:
                logger.with_extra(excluded_modules=excluded).info(
                    "Modules exclus par défaut (images)"
                )

        if not selected_modules:
            raise DomainValidationError("Aucun module à traiter")

        logger.with_extra(
            document_id=document_id,
            modules=selected_modules
        ).info("Modules sélectionnés pour génération")

        # Récupérer ou créer le tracking
        tracking = self._cards_storage.get_tracking(document_id, card_type)

        if tracking and not force:
            # Filtrer les modules déjà complétés
            completed_modules = [
                m for m, data in tracking.get("modules", {}).items()
                if data.get("status") == "completed"
            ]
            modules_to_process = [m for m in selected_modules if m not in completed_modules]

            if not modules_to_process:
                logger.info("Tous les modules sont déjà traités")
                return self._cards_storage.get_generation_metadata(document_id, card_type)

            logger.with_extra(
                skipped=completed_modules,
                remaining=modules_to_process
            ).info("Reprise après interruption")

            selected_modules = modules_to_process
        else:
            # Vérifier si déjà généré
            if not force and self._cards_storage.exists_for_restructuration(document_id, card_type):
                existing = self._cards_storage.get_generation_metadata(document_id, card_type)
                if existing:
                    logger.with_extra(document_id=document_id, card_type=card_type).warning(
                        "Génération existante"
                    )
                    raise GenerationAlreadyExistsError(
                        f"Cartes {card_type} déjà générées pour {document_id}. "
                        "Utilisez force=True."
                    )

            # Supprimer l'ancienne si force
            if force:
                self._cards_storage.delete(document_id, card_type)

            # Initialiser le tracking
            tracking = self._init_tracking(
                document_id, restructuration_id, card_type, selected_modules
            )
            self._cards_storage.save_tracking(document_id, card_type, tracking)

        # Restaurer le session_id depuis le tracking si disponible
        saved_session_id = tracking.get("session_id") if tracking else None
        if saved_session_id and hasattr(self._ai, 'set_session_id'):
            self._ai.set_session_id(saved_session_id, None)
            logger.with_extra(session_id=saved_session_id[:12]).info(
                "Session Claude restaurée depuis tracking"
            )

        # Récupérer le prompt système
        logger.debug("Récupération du prompt système")
        system_prompt = self._prompt_repo.get_system_prompt(self.SPECIALIST_ID)

        # Générer les cartes pour chaque module
        modules_processed = []
        cards_count = {}
        total_cards = 0

        for module in selected_modules:
            logger.with_extra(module=module).debug("Traitement du module")

            # Marquer le module en cours
            self._cards_storage.update_module_status(document_id, card_type, module, "in_progress")

            try:
                # Récupérer le contenu restructuré du module
                module_items = self._restructured_storage.get_module_items(document_id, module)

                if not module_items:
                    logger.with_extra(module=module).warning("Module sans contenu")
                    self._cards_storage.update_module_status(
                        document_id, card_type, module, "completed", cards_count=0
                    )
                    continue

                # Générer les cartes
                cards = self._generate_module_cards(
                    module_content=module_items,
                    module=module,
                    card_type=card_type,
                    system_prompt=system_prompt
                )

                # Sauvegarder chaque carte
                for idx, card in enumerate(cards, 1):
                    card_id = f"card-{idx}"
                    self._cards_storage.save_card(
                        document_id=document_id,
                        card_type=card_type,
                        module=module,
                        card_id=card_id,
                        content=card
                    )

                # Marquer le module comme terminé
                self._cards_storage.update_module_status(
                    document_id, card_type, module, "completed", cards_count=len(cards)
                )

                modules_processed.append(module)
                cards_count[module] = len(cards)
                total_cards += len(cards)

                # Sauvegarder le session_id après le premier module
                if hasattr(self._ai, 'get_session_id'):
                    current_session_id = self._ai.get_session_id()
                    if current_session_id and current_session_id != saved_session_id:
                        self._cards_storage.update_session_id(
                            document_id, card_type, current_session_id
                        )
                        saved_session_id = current_session_id
                        logger.with_extra(session_id=current_session_id[:12]).info(
                            "Session ID sauvegardé dans tracking"
                        )

                logger.with_extra(
                    module=module,
                    cards=len(cards)
                ).info("Module traité")

            except AIError as e:
                error_str = str(e).lower()

                # Vérifier si c'est une limite de tokens
                if self._is_rate_limit_error(error_str):
                    logger.with_extra(module=module).warning(
                        "Limite de tokens atteinte, tentative de reprise"
                    )

                    wait_time = self._handle_rate_limit()
                    if wait_time > 0:
                        logger.info(f"Attente de {wait_time}s avant reprise")
                        time.sleep(wait_time)

                        # Réessayer
                        try:
                            module_items = self._restructured_storage.get_module_items(
                                document_id, module
                            )
                            cards = self._generate_module_cards(
                                module_content=module_items,
                                module=module,
                                card_type=card_type,
                                system_prompt=system_prompt
                            )

                            for idx, card in enumerate(cards, 1):
                                card_id = f"card-{idx}"
                                self._cards_storage.save_card(
                                    document_id=document_id,
                                    card_type=card_type,
                                    module=module,
                                    card_id=card_id,
                                    content=card
                                )

                            self._cards_storage.update_module_status(
                                document_id, card_type, module, "completed", cards_count=len(cards)
                            )
                            modules_processed.append(module)
                            cards_count[module] = len(cards)
                            total_cards += len(cards)

                            logger.with_extra(module=module, cards=len(cards)).info(
                                "Module traité après reprise"
                            )
                            continue

                        except AIError as retry_error:
                            logger.error(f"Échec après reprise: {retry_error}")

                # Marquer le module comme échoué
                self._cards_storage.update_module_status(
                    document_id, card_type, module, "failed", error=str(e)
                )
                logger.with_extra(module=module, error=str(e)).error("Erreur IA sur module")
                raise

            except Exception as e:
                self._cards_storage.update_module_status(
                    document_id, card_type, module, "failed", error=str(e)
                )
                logger.with_extra(module=module, error=str(e)).warning(
                    "Erreur sur module, ignoré"
                )
                continue

        # Sauvegarder les métadonnées
        generation_id = str(uuid.uuid4())[:12]
        metadata = {
            "id": generation_id,
            "restructuration_id": restructuration_id,
            "document_id": document_id,
            "document_name": restructuration.get("document_name", ""),
            "card_type": card_type,
            "modules_processed": modules_processed,
            "cards_count": cards_count,
            "total_cards": total_cards,
            "generated_at": datetime.now().isoformat()
        }

        saved = self._cards_storage.save_generation_metadata(document_id, card_type, metadata)

        logger.with_extra(
            generation_id=generation_id,
            card_type=card_type,
            modules_count=len(modules_processed),
            total_cards=total_cards
        ).info("Génération terminée")

        return saved

    def _init_tracking(
        self,
        document_id: str,
        restructuration_id: str,
        card_type: str,
        modules: list[str]
    ) -> dict:
        """Initialise la structure de tracking."""
        now = datetime.now().isoformat()

        tracking = {
            "restructuration_id": restructuration_id,
            "document_id": document_id,
            "card_type": card_type,
            "specialist": self.SPECIALIST_ID,
            "started_at": now,
            "updated_at": now,
            "status": "in_progress",
            "modules": {}
        }

        for module in modules:
            tracking["modules"][module] = {
                "status": "pending",
                "cards_count": 0,
                "started_at": None,
                "completed_at": None,
                "error": None
            }

        return tracking

    def _generate_module_cards(
        self,
        module_content: list[dict],
        module: str,
        card_type: str,
        system_prompt: str
    ) -> list[dict]:
        """
        Génère des cartes pour un module via l'IA.

        Workflow:
        1. Récupérer le prompt de base du type de carte
        2. Récupérer le prompt spécifique au module
        3. Combiner les prompts et le contenu
        4. Envoyer au LLM
        5. Parser la réponse JSON

        Structure des prompts:
        - system.md : Prompt système général
        - {card_type}/{card_type}.md : Instructions de base pour ce type
        - {card_type}/{module}.md : Instructions spécifiques au module

        Args:
            module_content: Liste des items du module restructuré
            module: Nom du module
            card_type: Type de carte (basic, cloze)
            system_prompt: Prompt système du générateur

        Returns:
            Liste des cartes générées
        """
        prompt_specialist = f"{self.SPECIALIST_ID}/{card_type}"

        # Récupérer le prompt de base du type de carte (basic.md ou cloze.md)
        base_prompt = self._prompt_repo.get_module_prompt(prompt_specialist, card_type)

        # Récupérer le prompt spécifique au module
        module_prompt = self._prompt_repo.get_module_prompt(prompt_specialist, module)

        # Construire le contenu à envoyer
        content_json = json.dumps(module_content, ensure_ascii=False, indent=2)

        # Combiner: base prompt + module prompt + contenu
        user_message = f"{base_prompt}\n\n---\n\n{module_prompt}\n\n## Contenu à traiter\n\n```json\n{content_json}\n```"

        # LOG: Prompt envoyé
        logger.with_extra(
            module=module,
            card_type=card_type,
            content_items=len(module_content),
            base_prompt_length=len(base_prompt),
            module_prompt_length=len(module_prompt)
        ).info(f"Envoi prompt à l'IA ({card_type}.md + {module}.md)")

        # Appeler le LLM
        response = self._ai.send_message(
            user_message=user_message,
            system_prompt=system_prompt
        )

        # LOG: Réponse reçue
        logger.with_extra(
            module=module,
            response_length=len(response)
        ).info("Réponse IA reçue")

        return self._parse_cards(response, module, card_type)

    def _parse_cards(self, response: str, module: str, card_type: str) -> list[dict]:
        """
        Parse la réponse JSON du LLM pour extraire les cartes.

        Args:
            response: Réponse brute du LLM
            module: Nom du module
            card_type: Type de carte

        Returns:
            Liste des cartes

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
            cards = parsed.get("cards", [])

            # Valider la structure des cartes selon le type
            validated_cards = []
            for card in cards:
                if self._validate_card_structure(card, card_type):
                    validated_cards.append(card)
                else:
                    logger.with_extra(card=card).warning("Carte invalide ignorée")

            return validated_cards

        except json.JSONDecodeError as e:
            logger.error(f"JSON invalide pour {module}: {response[:500]}")
            raise AIError(f"JSON invalide pour {module}: {e}")

    def _validate_card_structure(self, card: dict, card_type: str) -> bool:
        """Valide la structure d'une carte selon son type."""
        if card_type == "basic":
            return "front" in card and "back" in card
        elif card_type == "cloze":
            return "text" in card
        return False

    def get_generation(self, generation_id: str) -> dict:
        """Récupère une génération par ID."""
        self._validate_id(generation_id, "generation_id")

        result = self._cards_storage.find_by_id(generation_id)
        if result is None:
            raise GenerationNotFoundError(f"Génération {generation_id} introuvable")
        return result

    def get_generation_by_restructuration(
        self,
        restructuration_id: str,
        card_type: str | None = None
    ) -> dict | None:
        """Récupère la génération d'une restructuration."""
        self._validate_id(restructuration_id, "restructuration_id")

        # Trouver la restructuration pour obtenir le document_id
        restructuration = self._restructured_storage.find_by_id(restructuration_id)
        if restructuration is None:
            return None

        document_id = restructuration["document_id"]
        return self._cards_storage.get_generation_metadata(document_id, card_type)

    def get_cards(
        self,
        generation_id: str,
        module: str | None = None
    ) -> list[dict]:
        """Récupère les cartes d'une génération."""
        self._validate_id(generation_id, "generation_id")

        generation = self._cards_storage.find_by_id(generation_id)
        if generation is None:
            raise GenerationNotFoundError(f"Génération {generation_id} introuvable")

        document_id = generation["document_id"]
        card_type = generation["card_type"]

        return self._cards_storage.get_cards(document_id, card_type, module)

    def get_card(self, generation_id: str, card_id: str) -> dict:
        """Récupère une carte spécifique."""
        self._validate_id(generation_id, "generation_id")

        generation = self._cards_storage.find_by_id(generation_id)
        if generation is None:
            raise GenerationNotFoundError(f"Génération {generation_id} introuvable")

        document_id = generation["document_id"]
        card_type = generation["card_type"]

        # Chercher la carte dans tous les modules
        for module in generation.get("modules_processed", []):
            card = self._cards_storage.get_card(document_id, card_type, module, card_id)
            if card is not None:
                return card

        raise CardNotFoundError(f"Carte {card_id} introuvable")

    def list_generations(self, document_id: str | None = None) -> list[dict]:
        """Liste les générations."""
        logger.debug("Liste des générations")
        return self._cards_storage.find_all(document_id)

    def delete_generation(self, generation_id: str) -> bool:
        """Supprime une génération."""
        self._validate_id(generation_id, "generation_id")

        logger.with_extra(generation_id=generation_id).info("Suppression génération")

        result = self._cards_storage.find_by_id(generation_id)
        if result is None:
            raise GenerationNotFoundError(f"Génération {generation_id} introuvable")

        return self._cards_storage.delete(result["document_id"], result["card_type"])

    def _validate_id(self, value: str, field_name: str) -> None:
        """Valide qu'un identifiant est non vide."""
        if not value or not isinstance(value, str) or value.strip() == "":
            raise DomainValidationError(
                f"Le {field_name} ne peut pas être vide ou invalide"
            )

    def _validate_card_type(self, card_type: str) -> None:
        """Valide le type de carte."""
        if card_type not in self.VALID_CARD_TYPES:
            raise DomainValidationError(
                f"Type de carte invalide: {card_type}. "
                f"Valeurs autorisées: {self.VALID_CARD_TYPES}"
            )

    def _is_rate_limit_error(self, error_str: str) -> bool:
        """Détecte si l'erreur est liée à une limite de tokens."""
        rate_limit_keywords = [
            "rate limit", "rate_limit", "token limit", "tokens limit",
            "quota", "too many requests", "429", "limit exceeded", "capacity"
        ]
        return any(keyword in error_str for keyword in rate_limit_keywords)

    def _handle_rate_limit(self) -> int:
        """Gère une erreur de rate limit."""
        try:
            usage = self._ai.check_usage()
            logger.with_extra(usage=usage).info("Usage tokens récupéré")

            reset_time = usage.get("reset_time")
            if reset_time:
                wait_seconds = self._parse_reset_time(reset_time)
                if wait_seconds > 0:
                    return wait_seconds + 10

            return 300  # 5 minutes par défaut

        except Exception as e:
            logger.warning(f"Impossible de vérifier /usage: {e}")
            return 300

    def _parse_reset_time(self, reset_time: str) -> int:
        """Parse une durée de reset en secondes."""
        total_seconds = 0

        hours_match = re.search(r"(\d+)h", reset_time)
        if hours_match:
            total_seconds += int(hours_match.group(1)) * 3600

        minutes_match = re.search(r"(\d+)m", reset_time)
        if minutes_match:
            total_seconds += int(minutes_match.group(1)) * 60

        seconds_match = re.search(r"(\d+)s", reset_time)
        if seconds_match:
            total_seconds += int(seconds_match.group(1))

        return total_seconds
