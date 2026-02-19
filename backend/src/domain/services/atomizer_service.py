"""
Service Atomizer (Optimiseur SuperMemo) du domaine.

Optimise les cartes Anki générées selon les règles SuperMemo:
- Atomisation (1 carte = 1 concept)
- Élimination des listes
- Simplification de la formulation
- Anti-interférence

PRINCIPE: Le service orchestre, les adapters implémentent.
"""
import json
import re
import time
import uuid
from datetime import datetime

from src.domain.exceptions import (
    DomainValidationError,
    AIError,
    GenerationNotFoundError,
    OptimizationNotFoundError,
    OptimizationAlreadyExistsError,
    CardNotFoundError
)
from src.ports.primary.optimize_cards_use_case import OptimizeCardsUseCase
from src.ports.secondary.cards_storage_port import CardsStoragePort
from src.ports.secondary.optimized_cards_storage_port import OptimizedCardsStoragePort
from src.ports.secondary.prompt_repository_port import PromptRepositoryPort
from src.ports.secondary.ai_port import AIPort
from src.infrastructure.logging.config import get_logger

logger = get_logger(__name__, "service")


class AtomizerService(OptimizeCardsUseCase):
    """
    Service métier pour l'optimisation SuperMemo des cartes.

    RESPONSABILITÉ: Orchestrer l'optimisation des cartes générées.

    DÉPENDANCES:
    - CardsStoragePort: Accès aux cartes générées
    - OptimizedCardsStoragePort: Persistance des cartes optimisées
    - PromptRepositoryPort: Récupération des prompts
    - AIPort: Communication avec le LLM
    """

    SPECIALIST_ID = "atomizer"
    VALID_CARD_TYPES = ["basic", "cloze"]
    # Types de contenu spécifiques (autres que general)
    CONTENT_TYPES = ["math_formulas", "code", "tables", "images"]

    def __init__(
        self,
        cards_storage: CardsStoragePort,
        optimized_storage: OptimizedCardsStoragePort,
        prompt_repository: PromptRepositoryPort,
        ai: AIPort
    ) -> None:
        """
        Injection des dépendances.

        Args:
            cards_storage: Port pour accéder aux cartes générées
            optimized_storage: Port pour persister les cartes optimisées
            prompt_repository: Port pour récupérer les prompts
            ai: Port pour communiquer avec le LLM
        """
        self._cards_storage = cards_storage
        self._optimized_storage = optimized_storage
        self._prompt_repo = prompt_repository
        self._ai = ai

    def optimize_cards(
        self,
        generation_id: str,
        content_types: list[str] | None = None,
        force: bool = False
    ) -> dict:
        """
        Optimise les cartes d'une génération selon SuperMemo.

        Workflow:
        1. Récupérer la génération et ses cartes
        2. Grouper les cartes par module
        3. Détecter le type de contenu (ou utiliser ceux spécifiés)
        4. Charger les prompts (system + general + type spécifique)
        5. Optimiser via IA
        6. Sauvegarder avec tracking

        Args:
            generation_id: Identifiant de la génération source
            content_types: Types de contenu à traiter (optionnel, sinon détection auto)
            force: Forcer la ré-optimisation

        Returns:
            Dict avec métadonnées de l'optimisation

        Raises:
            GenerationNotFoundError: Génération inexistante
            OptimizationAlreadyExistsError: Déjà optimisé
            AIError: Erreur IA
        """
        self._validate_id(generation_id, "generation_id")

        logger.with_extra(
            generation_id=generation_id,
            content_types=content_types,
            force=force
        ).info("Démarrage optimisation SuperMemo")

        # Récupérer la génération
        generation = self._cards_storage.find_by_id(generation_id)
        if generation is None:
            logger.with_extra(generation_id=generation_id).warning(
                "Génération introuvable"
            )
            raise GenerationNotFoundError(
                f"Génération {generation_id} introuvable"
            )

        document_id = generation["document_id"]
        card_type = generation["card_type"]
        modules_processed = generation.get("modules_processed", [])

        logger.with_extra(
            document_id=document_id,
            card_type=card_type,
            modules=modules_processed
        ).debug("Infos extraites de la génération")

        # Vérifier si déjà optimisé
        if not force and self._optimized_storage.exists_for_generation(document_id, card_type):
            existing = self._optimized_storage.get_optimization_metadata(document_id, card_type)
            if existing:
                logger.with_extra(document_id=document_id).warning(
                    "Optimisation existante"
                )
                raise OptimizationAlreadyExistsError(
                    f"Cartes {card_type} déjà optimisées pour {document_id}. "
                    "Utilisez force=True."
                )

        # Supprimer l'ancienne si force
        if force:
            self._optimized_storage.delete(document_id, card_type)

        # Récupérer le prompt système
        system_prompt = self._prompt_repo.get_system_prompt(self.SPECIALIST_ID)

        # Récupérer le prompt de base (general.md)
        prompt_specialist = f"{self.SPECIALIST_ID}/{card_type}"
        base_prompt = self._prompt_repo.get_module_prompt(prompt_specialist, "general")

        # Traiter chaque module
        total_input = 0
        total_output = 0
        modules_stats = {}

        for module in modules_processed:
            logger.with_extra(module=module).debug("Traitement du module")

            # Marquer le module en cours
            self._optimized_storage.update_module_status(
                document_id, card_type, module, "in_progress"
            )

            try:
                # Récupérer les cartes du module
                cards = self._cards_storage.get_cards(document_id, card_type, module)

                if not cards:
                    logger.with_extra(module=module).warning("Module sans cartes")
                    self._optimized_storage.update_module_status(
                        document_id, card_type, module, "completed",
                        cards_input=0, cards_output=0
                    )
                    continue

                cards_input = len(cards)

                # Détecter le type de contenu dominant
                detected_type = self._detect_content_type(cards, content_types)

                # Optimiser les cartes
                optimized_cards = self._optimize_module_cards(
                    cards=cards,
                    module=module,
                    card_type=card_type,
                    content_type=detected_type,
                    system_prompt=system_prompt,
                    base_prompt=base_prompt
                )

                # Sauvegarder les cartes optimisées
                for idx, card in enumerate(optimized_cards, 1):
                    card_id = f"card-{idx}"
                    self._optimized_storage.save_optimized_card(
                        document_id=document_id,
                        card_type=card_type,
                        module=module,
                        card_id=card_id,
                        content=card
                    )

                cards_output = len(optimized_cards)

                # Marquer le module comme terminé
                self._optimized_storage.update_module_status(
                    document_id, card_type, module, "completed",
                    cards_input=cards_input, cards_output=cards_output
                )

                modules_stats[module] = {
                    "input": cards_input,
                    "output": cards_output,
                    "content_type": detected_type
                }
                total_input += cards_input
                total_output += cards_output

                logger.with_extra(
                    module=module,
                    input=cards_input,
                    output=cards_output,
                    content_type=detected_type
                ).info("Module optimisé")

            except AIError as e:
                self._optimized_storage.update_module_status(
                    document_id, card_type, module, "failed", error=str(e)
                )
                logger.with_extra(module=module, error=str(e)).error(
                    "Erreur IA sur module"
                )
                raise

            except Exception as e:
                self._optimized_storage.update_module_status(
                    document_id, card_type, module, "failed", error=str(e)
                )
                logger.with_extra(module=module, error=str(e)).warning(
                    "Erreur sur module, ignoré"
                )
                continue

        # Calculer le ratio
        optimization_ratio = round(total_output / total_input, 2) if total_input > 0 else 0

        # Sauvegarder les métadonnées
        optimization_id = str(uuid.uuid4())[:12]
        metadata = {
            "id": optimization_id,
            "generation_id": generation_id,
            "document_id": document_id,
            "document_name": generation.get("document_name", ""),
            "card_type": card_type,
            "modules_processed": list(modules_stats.keys()),
            "modules_stats": modules_stats,
            "cards_input": total_input,
            "cards_output": total_output,
            "optimization_ratio": optimization_ratio,
            "optimized_at": datetime.now().isoformat()
        }

        saved = self._optimized_storage.save_optimization_metadata(
            document_id, card_type, metadata
        )

        logger.with_extra(
            optimization_id=optimization_id,
            input=total_input,
            output=total_output,
            ratio=optimization_ratio
        ).info("Optimisation terminée")

        return saved

    def _detect_content_type(
        self,
        cards: list[dict],
        specified_types: list[str] | None
    ) -> str:
        """
        Détecte le type de contenu dominant dans les cartes.

        Args:
            cards: Liste des cartes à analyser
            specified_types: Types spécifiés par l'utilisateur

        Returns:
            Type de contenu détecté (ou "general")
        """
        if specified_types and len(specified_types) == 1:
            return specified_types[0]

        # Analyse heuristique du contenu
        latex_count = 0
        code_count = 0
        table_count = 0
        image_count = 0

        for card in cards:
            content = json.dumps(card, ensure_ascii=False).lower()

            # Détection LaTeX
            if "[$]" in content or "[$$]" in content or "\\frac" in content:
                latex_count += 1

            # Détection code
            if "```" in content or "def " in content or "function" in content:
                code_count += 1

            # Détection tableaux
            if "|" in content and "---" in content:
                table_count += 1

            # Détection images
            if "image" in content or "figure" in content or "schéma" in content:
                image_count += 1

        total = len(cards)
        threshold = total * 0.3  # 30% des cartes

        if latex_count > threshold:
            return "math_formulas"
        elif code_count > threshold:
            return "code"
        elif table_count > threshold:
            return "tables"
        elif image_count > threshold:
            return "images"

        return "general"

    def _optimize_module_cards(
        self,
        cards: list[dict],
        module: str,
        card_type: str,
        content_type: str,
        system_prompt: str,
        base_prompt: str
    ) -> list[dict]:
        """
        Optimise les cartes d'un module via l'IA.

        Structure des prompts:
        - system.md : Règles SuperMemo générales
        - {card_type}/general.md : Instructions de base pour ce type
        - {card_type}/{content_type}.md : Instructions spécifiques (si applicable)

        Args:
            cards: Liste des cartes à optimiser
            module: Nom du module source
            card_type: Type de carte (basic, cloze)
            content_type: Type de contenu détecté
            system_prompt: Prompt système
            base_prompt: Prompt de base (general.md)

        Returns:
            Liste des cartes optimisées
        """
        prompt_specialist = f"{self.SPECIALIST_ID}/{card_type}"

        # Charger le prompt spécifique si ce n'est pas "general"
        type_prompt = ""
        if content_type != "general" and content_type in self.CONTENT_TYPES:
            try:
                type_prompt = self._prompt_repo.get_module_prompt(
                    prompt_specialist, content_type
                )
                type_prompt = f"\n\n---\n\n{type_prompt}"
            except Exception:
                logger.with_extra(content_type=content_type).warning(
                    "Prompt spécifique non trouvé, utilisation de general"
                )

        # Construire le contenu à envoyer
        cards_json = json.dumps(cards, ensure_ascii=False, indent=2)

        user_message = (
            f"{base_prompt}"
            f"{type_prompt}"
            f"\n\n## Cartes à optimiser\n\n```json\n{cards_json}\n```"
        )

        # Log descriptif des prompts utilisés
        prompts_used = "system.md + general.md"
        if content_type != "general" and type_prompt:
            prompts_used += f" + {content_type}.md"

        logger.with_extra(
            module=module,
            card_type=card_type,
            content_type=content_type,
            cards_count=len(cards)
        ).info(f"Envoi prompt à l'IA ({prompts_used})")

        # Appeler le LLM
        response = self._ai.send_message(
            user_message=user_message,
            system_prompt=system_prompt
        )

        logger.with_extra(
            module=module,
            response_length=len(response)
        ).info("Réponse IA reçue")

        return self._parse_optimized_cards(response, module, card_type)

    def _parse_optimized_cards(
        self,
        response: str,
        module: str,
        card_type: str
    ) -> list[dict]:
        """
        Parse la réponse JSON du LLM pour extraire les cartes optimisées.

        Args:
            response: Réponse brute du LLM
            module: Nom du module
            card_type: Type de carte

        Returns:
            Liste des cartes optimisées

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

    def get_optimization(self, optimization_id: str) -> dict:
        """Récupère une optimisation par ID."""
        self._validate_id(optimization_id, "optimization_id")

        result = self._optimized_storage.find_by_id(optimization_id)
        if result is None:
            raise OptimizationNotFoundError(
                f"Optimisation {optimization_id} introuvable"
            )
        return result

    def get_optimization_by_generation(
        self,
        generation_id: str
    ) -> dict | None:
        """Récupère l'optimisation d'une génération."""
        self._validate_id(generation_id, "generation_id")

        # Trouver la génération pour obtenir le document_id et card_type
        generation = self._cards_storage.find_by_id(generation_id)
        if generation is None:
            return None

        document_id = generation["document_id"]
        card_type = generation["card_type"]

        return self._optimized_storage.get_optimization_metadata(document_id, card_type)

    def get_optimized_cards(
        self,
        optimization_id: str,
        module: str | None = None
    ) -> list[dict]:
        """Récupère les cartes optimisées."""
        self._validate_id(optimization_id, "optimization_id")

        optimization = self._optimized_storage.find_by_id(optimization_id)
        if optimization is None:
            raise OptimizationNotFoundError(
                f"Optimisation {optimization_id} introuvable"
            )

        document_id = optimization["document_id"]
        card_type = optimization["card_type"]

        return self._optimized_storage.get_optimized_cards(
            document_id, card_type, module
        )

    def get_optimized_card(
        self,
        optimization_id: str,
        card_id: str
    ) -> dict:
        """Récupère une carte optimisée spécifique."""
        self._validate_id(optimization_id, "optimization_id")

        optimization = self._optimized_storage.find_by_id(optimization_id)
        if optimization is None:
            raise OptimizationNotFoundError(
                f"Optimisation {optimization_id} introuvable"
            )

        document_id = optimization["document_id"]
        card_type = optimization["card_type"]

        # Chercher la carte dans tous les modules
        for module in optimization.get("modules_processed", []):
            card = self._optimized_storage.get_optimized_card(
                document_id, card_type, module, card_id
            )
            if card is not None:
                return card

        raise CardNotFoundError(f"Carte {card_id} introuvable")

    def list_optimizations(self, document_id: str | None = None) -> list[dict]:
        """Liste les optimisations."""
        logger.debug("Liste des optimisations")
        return self._optimized_storage.find_all(document_id)

    def delete_optimization(self, optimization_id: str) -> bool:
        """Supprime une optimisation."""
        self._validate_id(optimization_id, "optimization_id")

        logger.with_extra(optimization_id=optimization_id).info(
            "Suppression optimisation"
        )

        result = self._optimized_storage.find_by_id(optimization_id)
        if result is None:
            raise OptimizationNotFoundError(
                f"Optimisation {optimization_id} introuvable"
            )

        return self._optimized_storage.delete(
            result["document_id"], result["card_type"]
        )

    def _validate_id(self, value: str, field_name: str) -> None:
        """Valide qu'un identifiant est non vide."""
        if not value or not isinstance(value, str) or value.strip() == "":
            raise DomainValidationError(
                f"Le {field_name} ne peut pas être vide ou invalide"
            )
