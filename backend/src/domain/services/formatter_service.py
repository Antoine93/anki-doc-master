"""
Service Formatter (Export Anki) du domaine.

Transforme les cartes optimisées en fichiers .txt importables
dans Anki avec la syntaxe appropriée :
- Headers Anki (#separator, #html, #notetype)
- Formatage HTML (<code>, <pre>, <br>)
- Préservation LaTeX et cloze
- Escaping des caractères spéciaux

PRINCIPE: Le service orchestre, les adapters implémentent.
"""
import json
import re
import uuid
from datetime import datetime

from src.domain.exceptions import (
    DomainValidationError,
    AIError,
    OptimizationNotFoundError,
    FormattingNotFoundError,
    FormattingAlreadyExistsError
)
from src.ports.primary.format_cards_use_case import FormatCardsUseCase
from src.ports.secondary.optimized_cards_storage_port import OptimizedCardsStoragePort
from src.ports.secondary.formatted_cards_storage_port import FormattedCardsStoragePort
from src.ports.secondary.prompt_repository_port import PromptRepositoryPort
from src.ports.secondary.ai_port import AIPort
from src.infrastructure.logging.config import get_logger

logger = get_logger(__name__, "service")


class FormatterService(FormatCardsUseCase):
    """
    Service métier pour l'export Anki des cartes.

    RESPONSABILITÉ: Orchestrer la transformation des cartes optimisées
    en fichiers .txt Anki importables.

    DÉPENDANCES:
    - OptimizedCardsStoragePort: Accès aux cartes optimisées
    - FormattedCardsStoragePort: Persistance des fichiers Anki
    - PromptRepositoryPort: Récupération des prompts
    - AIPort: Communication avec le LLM
    """

    SPECIALIST_ID = "formatter"
    VALID_CARD_TYPES = ["basic", "cloze"]

    def __init__(
        self,
        optimized_storage: OptimizedCardsStoragePort,
        formatted_storage: FormattedCardsStoragePort,
        prompt_repository: PromptRepositoryPort,
        ai: AIPort
    ) -> None:
        """
        Injection des dépendances.

        Args:
            optimized_storage: Port pour accéder aux cartes optimisées
            formatted_storage: Port pour persister les fichiers Anki
            prompt_repository: Port pour récupérer les prompts
            ai: Port pour communiquer avec le LLM
        """
        self._optimized_storage = optimized_storage
        self._formatted_storage = formatted_storage
        self._prompt_repo = prompt_repository
        self._ai = ai

    def format_cards(
        self,
        optimization_id: str,
        force: bool = False
    ) -> dict:
        """
        Formate les cartes optimisées en fichier Anki .txt.

        Workflow:
        1. Récupérer l'optimisation et ses cartes
        2. Vérifier si déjà formaté
        3. Charger les prompts (system + card_type)
        4. Envoyer à l'IA pour formatage
        5. Valider et sauvegarder le fichier .txt

        Args:
            optimization_id: Identifiant de l'optimisation source
            force: Forcer le re-formatage

        Returns:
            Dict avec métadonnées du formatage

        Raises:
            OptimizationNotFoundError: Optimisation inexistante
            FormattingAlreadyExistsError: Déjà formaté
            AIError: Erreur IA
        """
        self._validate_id(optimization_id, "optimization_id")

        logger.with_extra(
            optimization_id=optimization_id,
            force=force
        ).info("Démarrage formatage Anki")

        # Récupérer l'optimisation
        optimization = self._optimized_storage.find_by_id(optimization_id)
        if optimization is None:
            logger.with_extra(optimization_id=optimization_id).warning(
                "Optimisation introuvable"
            )
            raise OptimizationNotFoundError(
                f"Optimisation {optimization_id} introuvable"
            )

        document_id = optimization["document_id"]
        card_type = optimization["card_type"]
        modules_processed = optimization.get("modules_processed", [])

        logger.with_extra(
            document_id=document_id,
            card_type=card_type,
            modules=modules_processed
        ).debug("Infos extraites de l'optimisation")

        # Vérifier si déjà formaté
        if not force and self._formatted_storage.exists_for_optimization(
            document_id, card_type
        ):
            existing = self._formatted_storage.get_formatting_metadata(
                document_id, card_type
            )
            if existing:
                logger.with_extra(document_id=document_id).warning(
                    "Formatage existant"
                )
                raise FormattingAlreadyExistsError(
                    f"Cartes {card_type} déjà formatées pour {document_id}. "
                    "Utilisez force=True."
                )

        # Supprimer l'ancien si force
        if force:
            self._formatted_storage.delete(document_id, card_type)

        # Récupérer toutes les cartes optimisées
        all_cards = self._optimized_storage.get_optimized_cards(
            document_id, card_type
        )

        if not all_cards:
            raise DomainValidationError(
                f"Aucune carte optimisée pour {document_id}/{card_type}"
            )

        logger.with_extra(
            cards_count=len(all_cards)
        ).debug("Cartes optimisées récupérées")

        # Charger les prompts
        system_prompt = self._prompt_repo.get_system_prompt(self.SPECIALIST_ID)
        card_type_prompt = self._prompt_repo.get_module_prompt(
            self.SPECIALIST_ID, card_type
        )

        # Préparer les cartes pour l'IA
        cards_json = json.dumps(all_cards, ensure_ascii=False, indent=2)

        user_message = (
            f"{card_type_prompt}\n\n"
            f"## Cartes à formater\n\n```json\n{cards_json}\n```"
        )

        logger.with_extra(
            card_type=card_type,
            cards_count=len(all_cards)
        ).info("Envoi prompt à l'IA")

        # Appeler le LLM
        response = self._ai.send_message(
            user_message=user_message,
            system_prompt=system_prompt
        )

        logger.with_extra(
            response_length=len(response)
        ).info("Réponse IA reçue")

        # Extraire et valider le contenu formaté
        formatted_content = self._extract_formatted_content(
            response, card_type, len(all_cards)
        )

        # Sauvegarder le fichier
        output_path = self._formatted_storage.save_formatted_file(
            document_id=document_id,
            card_type=card_type,
            content=formatted_content
        )

        # Compter les cartes dans le fichier
        cards_count = self._count_cards_in_file(formatted_content, card_type)

        # Sauvegarder les métadonnées
        formatting_id = str(uuid.uuid4())[:12]
        metadata = {
            "id": formatting_id,
            "optimization_id": optimization_id,
            "document_id": document_id,
            "document_name": optimization.get("document_name", ""),
            "card_type": card_type,
            "cards_count": cards_count,
            "output_file": output_path,
            "formatted_at": datetime.now().isoformat()
        }

        saved = self._formatted_storage.save_formatting_metadata(
            document_id, card_type, metadata
        )

        logger.with_extra(
            formatting_id=formatting_id,
            cards_count=cards_count,
            output_file=output_path
        ).info("Formatage terminé")

        return saved

    def _extract_formatted_content(
        self,
        response: str,
        card_type: str,
        expected_count: int
    ) -> str:
        """
        Extrait le contenu formaté de la réponse IA.

        Args:
            response: Réponse brute du LLM
            card_type: Type de carte
            expected_count: Nombre de cartes attendu

        Returns:
            Contenu texte formaté pour Anki

        Raises:
            AIError: Si le parsing échoue
        """
        response = response.strip()

        if not response:
            raise AIError("Réponse vide du LLM")

        # Extraire du bloc markdown si présent
        if "```" in response:
            # Chercher un bloc de code
            match = re.search(r"```(?:txt|text|anki)?\s*\n(.*?)```", response, re.DOTALL)
            if match:
                response = match.group(1).strip()
            else:
                # Essayer sans spécification de langage
                start = response.find("```") + 3
                # Sauter jusqu'à la fin de la première ligne
                start = response.find("\n", start) + 1
                end = response.rfind("```")
                if end > start:
                    response = response[start:end].strip()

        # Valider les headers Anki
        lines = response.split("\n")
        if not lines:
            raise AIError("Contenu formaté vide")

        # Vérifier la présence des headers obligatoires
        has_separator = any(
            line.strip().startswith("#separator") for line in lines[:3]
        )
        has_html = any(
            line.strip().startswith("#html") for line in lines[:3]
        )

        if not has_separator or not has_html:
            logger.warning(
                f"Headers manquants, ajout automatique. "
                f"separator={has_separator}, html={has_html}"
            )
            # Ajouter les headers si manquants
            headers = ["#separator:;", "#html:true"]
            if card_type == "cloze":
                headers.append("#notetype:Cloze")
            response = "\n".join(headers) + "\n" + response

        return response

    def _count_cards_in_file(self, content: str, card_type: str) -> int:
        """
        Compte le nombre de cartes dans le fichier formaté.

        Args:
            content: Contenu du fichier
            card_type: Type de carte

        Returns:
            Nombre de cartes
        """
        lines = content.strip().split("\n")
        # Filtrer les headers (lignes commençant par #)
        card_lines = [
            line for line in lines
            if line.strip() and not line.strip().startswith("#")
        ]
        return len(card_lines)

    def get_formatting(self, formatting_id: str) -> dict:
        """Récupère un formatage par ID."""
        self._validate_id(formatting_id, "formatting_id")

        result = self._formatted_storage.find_by_id(formatting_id)
        if result is None:
            raise FormattingNotFoundError(
                f"Formatage {formatting_id} introuvable"
            )
        return result

    def get_formatting_by_optimization(
        self,
        optimization_id: str
    ) -> dict | None:
        """Récupère le formatage d'une optimisation."""
        self._validate_id(optimization_id, "optimization_id")

        # Trouver l'optimisation pour obtenir document_id et card_type
        optimization = self._optimized_storage.find_by_id(optimization_id)
        if optimization is None:
            return None

        document_id = optimization["document_id"]
        card_type = optimization["card_type"]

        return self._formatted_storage.get_formatting_metadata(
            document_id, card_type
        )

    def get_formatted_content(self, formatting_id: str) -> str:
        """Récupère le contenu du fichier Anki formaté."""
        self._validate_id(formatting_id, "formatting_id")

        formatting = self._formatted_storage.find_by_id(formatting_id)
        if formatting is None:
            raise FormattingNotFoundError(
                f"Formatage {formatting_id} introuvable"
            )

        document_id = formatting["document_id"]
        card_type = formatting["card_type"]

        content = self._formatted_storage.get_formatted_content(
            document_id, card_type
        )

        if content is None:
            raise FormattingNotFoundError(
                f"Fichier Anki pour {formatting_id} introuvable"
            )

        return content

    def list_formattings(self, document_id: str | None = None) -> list[dict]:
        """Liste les formatages."""
        logger.debug("Liste des formatages")
        return self._formatted_storage.find_all(document_id)

    def delete_formatting(self, formatting_id: str) -> bool:
        """Supprime un formatage."""
        self._validate_id(formatting_id, "formatting_id")

        logger.with_extra(formatting_id=formatting_id).info(
            "Suppression formatage"
        )

        result = self._formatted_storage.find_by_id(formatting_id)
        if result is None:
            raise FormattingNotFoundError(
                f"Formatage {formatting_id} introuvable"
            )

        return self._formatted_storage.delete(
            result["document_id"], result["card_type"]
        )

    def _validate_id(self, value: str, field_name: str) -> None:
        """Valide qu'un identifiant est non vide."""
        if not value or not isinstance(value, str) or value.strip() == "":
            raise DomainValidationError(
                f"Le {field_name} ne peut pas être vide ou invalide"
            )
