"""
Adapter pour session Claude interactive persistante.

Maintient une session Claude ouverte pour réutiliser le contexte
(PDF chargé une seule fois, conversation continue).

ARCHITECTURE:
- subprocess.Popen pour garder le processus ouvert
- Communication via stdin/stdout
- Détection de fin de réponse via marqueur
"""
import subprocess
import threading
import queue
import time
import re
from pathlib import Path

from src.ports.secondary.ai_port import AIPort
from src.domain.exceptions import AIError
from src.infrastructure.logging.config import get_logger

logger = get_logger(__name__, "adapter")

# Marqueur de fin de réponse (demandé dans chaque prompt)
END_MARKER = "<<<END_RESPONSE>>>"


class ClaudeInteractiveAdapter(AIPort):
    """
    Session Claude interactive persistante.

    Le PDF est chargé une seule fois au démarrage de la session.
    Tous les messages suivants réutilisent le même contexte.
    """

    def __init__(self, timeout: int = 300, working_dir: str | None = None) -> None:
        """
        Initialise l'adapter interactif.

        Args:
            timeout: Timeout en secondes pour chaque réponse (défaut: 5 min)
            working_dir: Répertoire de travail pour Claude
        """
        self._timeout = timeout
        self._working_dir = working_dir
        self._process: subprocess.Popen | None = None
        self._output_queue: queue.Queue = queue.Queue()
        self._reader_thread: threading.Thread | None = None
        self._session_active = False
        self._current_pdf: str | None = None  # PDF actuellement chargé

    def start_session(self, pdf_path: str | None = None) -> None:
        """
        Démarre une session Claude interactive.

        Args:
            pdf_path: Chemin du PDF à charger (optionnel)
        """
        if self._session_active:
            logger.warning("Session déjà active, fermeture de l'ancienne")
            self.close_session()

        cmd = ["claude"]
        if pdf_path:
            # Vérifier que le PDF existe
            if not Path(pdf_path).exists():
                raise AIError(f"PDF introuvable: {pdf_path}")
            cmd.append(pdf_path)

        logger.with_extra(pdf=pdf_path).info("Démarrage session Claude interactive")

        self._current_pdf = pdf_path

        try:
            self._process = subprocess.Popen(
                cmd,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                bufsize=1,  # Line buffered
                cwd=self._working_dir
            )
            self._session_active = True

            # Démarrer le thread de lecture
            self._start_reader_thread()

            # Attendre que Claude soit prêt (lire le message initial s'il y en a)
            time.sleep(1)
            self._flush_output()

            logger.info("Session Claude démarrée")

        except FileNotFoundError:
            raise AIError("Claude CLI non trouvé. Installez-le avec: npm install -g @anthropic-ai/claude-cli")
        except Exception as e:
            raise AIError(f"Erreur démarrage session: {e}")

    def _start_reader_thread(self) -> None:
        """Démarre le thread de lecture stdout."""
        def reader():
            try:
                while self._session_active and self._process:
                    line = self._process.stdout.readline()
                    if line:
                        self._output_queue.put(line)
                    elif self._process.poll() is not None:
                        # Process terminé
                        break
            except Exception as e:
                logger.error(f"Erreur reader thread: {e}")

        self._reader_thread = threading.Thread(target=reader, daemon=True)
        self._reader_thread.start()

    def _flush_output(self) -> str:
        """Vide la queue de sortie et retourne le contenu."""
        output = []
        while not self._output_queue.empty():
            try:
                output.append(self._output_queue.get_nowait())
            except queue.Empty:
                break
        return "".join(output)

    def _read_until_marker(self, timeout: int | None = None) -> str:
        """
        Lit la sortie jusqu'au marqueur de fin ou timeout.

        Args:
            timeout: Timeout en secondes (défaut: self._timeout)

        Returns:
            Réponse de Claude (sans le marqueur)
        """
        timeout = timeout or self._timeout
        start_time = time.time()
        output_lines = []

        while True:
            elapsed = time.time() - start_time
            if elapsed > timeout:
                logger.warning(f"Timeout après {timeout}s")
                break

            try:
                line = self._output_queue.get(timeout=1)
                output_lines.append(line)

                # Vérifier si on a le marqueur de fin
                if END_MARKER in line:
                    break

            except queue.Empty:
                # Vérifier si le process est toujours actif
                if self._process and self._process.poll() is not None:
                    logger.error("Process Claude terminé inopinément")
                    self._session_active = False
                    raise AIError("Session Claude terminée")
                continue

        # Assembler la réponse et retirer le marqueur
        response = "".join(output_lines)
        response = response.replace(END_MARKER, "").strip()

        return response

    def send_message(
        self,
        user_message: str,
        system_prompt: str = "",
        max_tokens: int = 4096
    ) -> str:
        """
        Envoie un message dans la session active.

        Args:
            user_message: Message utilisateur
            system_prompt: Prompt système (ignoré après le premier message)
            max_tokens: Non utilisé en mode CLI

        Returns:
            Réponse de Claude
        """
        if not self._session_active or not self._process:
            raise AIError("Aucune session active. Appelez start_session() d'abord.")

        # Construire le prompt avec marqueur de fin
        prompt = user_message
        if system_prompt:
            prompt = f"{system_prompt}\n\n{user_message}"

        # Ajouter l'instruction de marqueur de fin
        prompt += f"\n\n[IMPORTANT: Termine ta réponse par exactement: {END_MARKER}]"

        logger.debug(f"Envoi message ({len(prompt)} chars)")

        try:
            # Envoyer le message
            self._process.stdin.write(prompt + "\n")
            self._process.stdin.flush()

            # Lire la réponse
            response = self._read_until_marker()

            logger.debug(f"Réponse reçue ({len(response)} chars)")
            return response

        except BrokenPipeError:
            self._session_active = False
            raise AIError("Session Claude fermée (broken pipe)")
        except Exception as e:
            raise AIError(f"Erreur envoi message: {e}")

    def send_message_with_pdf(
        self,
        pdf_path: str,
        user_message: str,
        system_prompt: str,
        max_tokens: int = 4096
    ) -> str:
        """
        Envoie un message avec PDF.

        Si pas de session active, en démarre une avec le PDF.
        Si session active avec un PDF différent, redémarre avec le nouveau PDF.
        Sinon, utilise la session existante (PDF déjà chargé).
        """
        # Normaliser le chemin pour comparaison
        pdf_path_normalized = str(Path(pdf_path).resolve())
        current_pdf_normalized = str(Path(self._current_pdf).resolve()) if self._current_pdf else None

        if not self._session_active:
            self.start_session(pdf_path)
        elif current_pdf_normalized != pdf_path_normalized:
            # PDF différent, redémarrer la session
            logger.info(f"PDF différent détecté, redémarrage session")
            self.close_session()
            self.start_session(pdf_path)

        return self.send_message(user_message, system_prompt, max_tokens)

    def get_current_pdf(self) -> str | None:
        """Retourne le chemin du PDF actuellement chargé."""
        return self._current_pdf

    def check_usage(self) -> dict:
        """
        Vérifie l'utilisation des tokens via /usage.

        Returns:
            Dict avec les infos d'utilisation
        """
        if not self._session_active:
            raise AIError("Aucune session active")

        logger.info("Vérification usage tokens")

        try:
            self._process.stdin.write("/usage\n")
            self._process.stdin.flush()

            # Lire la réponse (pas de marqueur pour les commandes système)
            time.sleep(2)
            response = self._flush_output()

            # Parser la réponse /usage
            usage = self._parse_usage(response)
            logger.with_extra(usage=usage).info("Usage récupéré")
            return usage

        except Exception as e:
            logger.error(f"Erreur check_usage: {e}")
            return {"error": str(e)}

    def _parse_usage(self, response: str) -> dict:
        """Parse la réponse de /usage."""
        usage = {
            "raw": response,
            "tokens_used": None,
            "tokens_limit": None,
            "reset_time": None
        }

        # Patterns à adapter selon le format réel de /usage
        # Exemple: "Tokens: 1234/10000, Reset: 2h30m"
        tokens_match = re.search(r"(\d+)\s*/\s*(\d+)", response)
        if tokens_match:
            usage["tokens_used"] = int(tokens_match.group(1))
            usage["tokens_limit"] = int(tokens_match.group(2))

        time_match = re.search(r"reset.*?(\d+[hm][\d+m]*)", response, re.IGNORECASE)
        if time_match:
            usage["reset_time"] = time_match.group(1)

        return usage

    def is_session_active(self) -> bool:
        """Vérifie si une session est active."""
        return self._session_active and self._process is not None

    def close_session(self) -> None:
        """Ferme la session Claude."""
        if self._process:
            logger.info("Fermeture session Claude")
            try:
                self._process.stdin.write("/exit\n")
                self._process.stdin.flush()
                self._process.wait(timeout=5)
            except Exception:
                self._process.terminate()
            finally:
                self._process = None

        self._session_active = False
        self._current_pdf = None

    def __del__(self):
        """Nettoyage à la destruction."""
        self.close_session()
