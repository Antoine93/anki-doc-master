"""
Adapter Claude avec session persistante via session_id.

Workflow:
1. Premier appel avec --output-format json → capture session_id
2. Appels suivants avec --resume $SESSION_ID → contexte conservé

Le PDF est chargé une seule fois, le contexte est conservé.
"""
import subprocess
import json
import re
from pathlib import Path

from src.ports.secondary.ai_port import AIPort
from src.domain.exceptions import AIError
from src.infrastructure.logging.config import get_logger

logger = get_logger(__name__, "adapter")


class ClaudeSessionAdapter(AIPort):
    """
    Adapter Claude utilisant session_id pour conserver le contexte.

    Le premier appel capture le session_id, les suivants le réutilisent.
    """

    def __init__(self, timeout: int = 300, working_dir: str | None = None) -> None:
        self._timeout = timeout
        self._working_dir = working_dir
        self._session_id: str | None = None
        self._current_pdf: str | None = None

    def _run_claude(
        self,
        prompt: str,
        pdf_path: str | None = None,
        capture_session: bool = False
    ) -> str:
        """
        Exécute Claude CLI.

        Args:
            prompt: Le prompt à envoyer
            pdf_path: Chemin du PDF (optionnel)
            capture_session: Si True, capture le session_id du JSON

        Returns:
            Réponse de Claude
        """
        cmd = ["claude", "-p", prompt]

        # Ajouter le PDF si fourni
        if pdf_path:
            cmd.append(pdf_path)

        # Si on a déjà une session, la reprendre
        if self._session_id and not capture_session:
            cmd.extend(["--resume", self._session_id])
            logger.debug(f"Reprise session {self._session_id[:8]}...")
        elif capture_session:
            # Premier appel : capturer le session_id
            cmd.extend(["--output-format", "json"])

        logger.with_extra(
            has_session=bool(self._session_id),
            has_pdf=bool(pdf_path),
            capture_session=capture_session
        ).debug("Appel Claude CLI")

        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                encoding="utf-8",
                timeout=self._timeout,
                cwd=self._working_dir
            )

            if result.returncode != 0:
                error_msg = result.stderr or result.stdout
                logger.error(f"Erreur Claude CLI (code {result.returncode}): {error_msg[:300]}")
                raise AIError(f"Erreur Claude CLI (code {result.returncode}): {error_msg}")

            output = result.stdout.strip()

            if not output:
                raise AIError("Réponse vide de Claude CLI")

            # Si on capture la session, parser le JSON
            if capture_session:
                return self._parse_json_response(output)

            return output

        except subprocess.TimeoutExpired:
            raise AIError(f"Timeout après {self._timeout}s")
        except FileNotFoundError:
            raise AIError("Claude CLI non trouvé")

    def _parse_json_response(self, output: str) -> str:
        """
        Parse la réponse JSON et extrait le session_id.

        Args:
            output: Sortie JSON de Claude

        Returns:
            Le contenu de la réponse (result)
        """
        try:
            # Nettoyer les caractères de contrôle
            cleaned = re.sub(r'[\x00-\x1f]', '', output)
            data = json.loads(cleaned)

            # Capturer le session_id
            session_id = data.get("session_id")
            if session_id:
                self._session_id = session_id
                logger.with_extra(session_id=session_id[:12]).info(
                    "Session ID capturé"
                )

            # Retourner le résultat
            result = data.get("result", "")
            if not result:
                # Parfois c'est dans 'content' ou 'message'
                result = data.get("content", data.get("message", str(data)))

            return result

        except json.JSONDecodeError as e:
            logger.warning(f"JSON parse error: {e}, returning raw output")
            return output

    def send_message(
        self,
        user_message: str,
        system_prompt: str = "",
        max_tokens: int = 4096
    ) -> str:
        """Envoie un message dans la session existante."""
        prompt = user_message
        if system_prompt:
            prompt = f"{system_prompt}\n\n{user_message}"

        # Si pas de session, c'est le premier appel
        capture_session = self._session_id is None

        return self._run_claude(prompt, capture_session=capture_session)

    def send_message_with_pdf(
        self,
        pdf_path: str,
        user_message: str,
        system_prompt: str,
        max_tokens: int = 4096
    ) -> str:
        """
        Envoie un message avec PDF.

        Si c'est un nouveau PDF, démarre une nouvelle session.
        Sinon, réutilise la session existante.
        """
        prompt = f"{system_prompt}\n\n{user_message}"

        # Normaliser le chemin de manière robuste (gère Windows/Unix)
        pdf_normalized = str(Path(pdf_path).resolve()).replace("\\", "/").lower()
        current_normalized = (
            str(Path(self._current_pdf).resolve()).replace("\\", "/").lower()
            if self._current_pdf else None
        )

        # Nouveau PDF = nouvelle session
        if pdf_normalized != current_normalized:
            logger.with_extra(
                new_pdf=pdf_normalized[-50:] if pdf_normalized else None,
                current_pdf=current_normalized[-50:] if current_normalized else None
            ).info("Nouveau PDF détecté, démarrage nouvelle session")
            self._session_id = None
            self._current_pdf = pdf_path

            # Premier appel avec PDF et capture session
            return self._run_claude(prompt, pdf_path=pdf_path, capture_session=True)

        # Même PDF, réutiliser la session
        if self._session_id:
            logger.debug("Réutilisation session existante (PDF déjà chargé)")
            return self._run_claude(prompt, capture_session=False)
        else:
            # Pas de session mais même PDF (ne devrait pas arriver)
            return self._run_claude(prompt, pdf_path=pdf_path, capture_session=True)

    def start_session(self, pdf_path: str | None = None) -> None:
        """Démarre une nouvelle session."""
        self._session_id = None
        self._current_pdf = pdf_path

        if pdf_path:
            # Envoyer un message initial pour créer la session
            self._run_claude(
                "Analyse ce document. Réponds 'Prêt.' quand tu as terminé.",
                pdf_path=pdf_path,
                capture_session=True
            )

    def is_session_active(self) -> bool:
        """Vérifie si une session est active."""
        return self._session_id is not None

    def get_session_id(self) -> str | None:
        """Retourne l'ID de session actuel."""
        return self._session_id

    def set_session_id(self, session_id: str, pdf_path: str | None = None) -> None:
        """
        Injecte un session_id existant (reprise depuis tracking).

        Args:
            session_id: ID de session à réutiliser
            pdf_path: Chemin du PDF associé
        """
        self._session_id = session_id
        self._current_pdf = pdf_path
        logger.with_extra(session_id=session_id[:12]).info(
            "Session ID injecté depuis tracking"
        )

    def get_current_pdf(self) -> str | None:
        """Retourne le PDF actuel."""
        return self._current_pdf

    def close_session(self) -> None:
        """Ferme la session."""
        self._session_id = None
        self._current_pdf = None
        logger.info("Session fermée")

    def check_usage(self) -> dict:
        """Non supporté en mode CLI standard."""
        return {"error": "check_usage non supporté en mode session_id"}
