"""
Port secondaire pour la communication IA.

Interface TECHNIQUE pure pour communiquer avec un LLM.
Aucune logique métier, aucun prompt spécifique.

Supporte deux modes:
- One-shot: Chaque appel est indépendant (mode legacy)
- Session: Conversation persistante avec contexte conservé
"""
from abc import ABC, abstractmethod


class AIPort(ABC):
    """
    Interface technique pour communiquer avec un LLM.

    RESPONSABILITÉ: Envoyer des messages, recevoir des réponses.
    Aucun prompt métier ici - c'est un "tuyau" de communication.

    MODES:
    - One-shot: send_message() / send_message_with_pdf() isolés
    - Session: start_session() puis send_message() multiples
    """

    @abstractmethod
    def send_message(
        self,
        user_message: str,
        system_prompt: str,
        max_tokens: int = 4096
    ) -> str:
        """
        Envoie un message texte au LLM.

        Args:
            user_message: Message utilisateur
            system_prompt: Prompt système
            max_tokens: Nombre maximum de tokens en réponse

        Returns:
            Réponse textuelle brute du LLM

        Raises:
            AIError: Si la communication échoue
        """
        pass

    @abstractmethod
    def send_message_with_pdf(
        self,
        pdf_path: str,
        user_message: str,
        system_prompt: str,
        max_tokens: int = 4096
    ) -> str:
        """
        Envoie un message avec un PDF attaché au LLM.

        Args:
            pdf_path: Chemin absolu vers le fichier PDF
            user_message: Message utilisateur
            system_prompt: Prompt système
            max_tokens: Nombre maximum de tokens en réponse

        Returns:
            Réponse textuelle brute du LLM

        Raises:
            AIError: Si la communication échoue
        """
        pass

    # --- Méthodes de session (optionnelles, avec implémentations par défaut) ---

    def start_session(self, pdf_path: str | None = None) -> None:
        """
        Démarre une session interactive persistante.

        Args:
            pdf_path: PDF à charger dans la session (optionnel)

        Note: Implémentation par défaut = no-op (mode one-shot)
        """
        pass

    def is_session_active(self) -> bool:
        """
        Vérifie si une session est active.

        Returns:
            True si session active, False sinon
        """
        return False

    def close_session(self) -> None:
        """Ferme la session active."""
        pass

    def check_usage(self) -> dict:
        """
        Vérifie l'utilisation des tokens.

        Returns:
            Dict avec tokens_used, tokens_limit, reset_time
        """
        return {"tokens_used": None, "tokens_limit": None, "reset_time": None}
