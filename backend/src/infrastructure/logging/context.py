"""
Context pour le Correlation ID.

Utilise contextvars pour un stockage thread-safe et async-safe
du correlation_id unique par requête.
"""
import contextvars
import uuid

# Variable de contexte pour le correlation ID (thread-safe et async-safe)
_correlation_id: contextvars.ContextVar[str] = contextvars.ContextVar(
    "correlation_id",
    default=""
)


def generate_correlation_id() -> str:
    """Génère un nouveau correlation ID unique."""
    return str(uuid.uuid4())


def set_correlation_id(correlation_id: str) -> contextvars.Token:
    """
    Définit le correlation ID pour le contexte actuel.

    Args:
        correlation_id: L'ID à définir

    Returns:
        Token pour restaurer la valeur précédente si nécessaire
    """
    return _correlation_id.set(correlation_id)


def get_correlation_id() -> str:
    """
    Récupère le correlation ID du contexte actuel.

    Returns:
        Le correlation ID ou chaîne vide si non défini
    """
    return _correlation_id.get()


def reset_correlation_id(token: contextvars.Token) -> None:
    """Restaure le correlation ID précédent."""
    _correlation_id.reset(token)
