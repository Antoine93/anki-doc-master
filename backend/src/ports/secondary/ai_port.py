"""
Port secondaire pour la communication IA.

Interface TECHNIQUE pure pour communiquer avec un LLM.
Aucune logique métier, aucun prompt spécifique.
"""
from abc import ABC, abstractmethod


class AIPort(ABC):
    """
    Interface technique pour communiquer avec un LLM.

    RESPONSABILITÉ: Envoyer des messages, recevoir des réponses.
    Aucun prompt métier ici - c'est un "tuyau" de communication.

    Les prompts et parsing sont dans les adapters métier
    (ex: ClaudeAnalystAdapter) qui UTILISENT ce port.
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
