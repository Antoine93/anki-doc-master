"""
Adapter secondaire pour la communication CLI avec Claude.

Implémente AIPort pour la communication technique pure.
Aucun prompt métier ici - c'est un "tuyau" de communication.

RESPONSABILITÉ:
- Exécuter les commandes CLI
- Gérer les timeouts et erreurs de communication
- Retourner les réponses brutes
"""
import subprocess

from src.ports.secondary.ai_port import AIPort
from src.domain.exceptions import AIError
from src.infrastructure.logging.config import get_logger

logger = get_logger(__name__, "adapter")


class ClaudeCliAdapter(AIPort):
    """
    Implémentation CLI pour communiquer avec Claude.

    Utilise la commande `claude -p` pour envoyer des requêtes.
    Aucun prompt spécifique - c'est un canal de communication.
    """

    def __init__(self, timeout: int = 300, working_dir: str | None = None) -> None:
        """
        Initialise l'adapter CLI.

        Args:
            timeout: Timeout en secondes pour les commandes (défaut: 5 min)
            working_dir: Répertoire de travail pour Claude
        """
        self._timeout = timeout
        self._working_dir = working_dir

    def send_message(
        self,
        user_message: str,
        system_prompt: str,
        max_tokens: int = 4096
    ) -> str:
        """Envoie un message simple à Claude via CLI."""
        full_prompt = f"{system_prompt}\n\n{user_message}"

        logger.debug("Envoi message à Claude CLI")

        try:
            result = subprocess.run(
                ["claude", "-p", full_prompt],
                capture_output=True,
                text=True,
                timeout=self._timeout,
                cwd=self._working_dir
            )

            if result.returncode != 0:
                error_msg = result.stderr or result.stdout
                logger.error(f"Erreur Claude CLI: {error_msg[:300]}")
                raise AIError(f"Erreur Claude CLI: {error_msg}")

            logger.debug(f"Réponse reçue ({len(result.stdout)} chars)")
            return result.stdout.strip()

        except subprocess.TimeoutExpired:
            logger.error(f"Timeout après {self._timeout}s")
            raise AIError(f"Timeout après {self._timeout}s")
        except FileNotFoundError:
            logger.error("Claude CLI non trouvé")
            raise AIError("Claude CLI non trouvé. Installez-le avec: npm install -g @anthropic-ai/claude-cli")

    def send_message_with_pdf(
        self,
        pdf_path: str,
        user_message: str,
        system_prompt: str,
        max_tokens: int = 4096
    ) -> str:
        """Envoie un message avec un PDF attaché à Claude via CLI."""
        full_prompt = f"{system_prompt}\n\n{user_message}"

        logger.with_extra(pdf=pdf_path).debug("Envoi message avec PDF à Claude CLI")

        try:
            result = subprocess.run(
                ["claude", "-p", full_prompt, pdf_path],
                capture_output=True,
                text=True,
                timeout=self._timeout,
                cwd=self._working_dir
            )

            if result.stderr:
                logger.warning(f"Stderr: {result.stderr[:300]}")

            if result.returncode != 0:
                error_msg = result.stderr or result.stdout
                logger.error(f"Erreur Claude CLI (code {result.returncode}): {error_msg[:300]}")
                raise AIError(f"Erreur Claude CLI (code {result.returncode}): {error_msg}")

            if not result.stdout.strip():
                logger.error("Réponse vide de Claude CLI")
                raise AIError("Réponse vide de Claude CLI")

            logger.debug(f"Réponse reçue ({len(result.stdout)} chars)")
            return result.stdout.strip()

        except subprocess.TimeoutExpired:
            logger.error(f"Timeout après {self._timeout}s")
            raise AIError(f"Timeout après {self._timeout}s")
        except FileNotFoundError:
            logger.error("Claude CLI non trouvé")
            raise AIError("Claude CLI non trouvé. Installez-le avec: npm install -g @anthropic-ai/claude-cli")
