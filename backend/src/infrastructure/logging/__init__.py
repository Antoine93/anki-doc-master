"""
Infrastructure de logging centralisée.

Fournit le logging structuré JSON avec correlation_id
pour la traçabilité des requêtes de bout en bout.
"""
from src.infrastructure.logging.config import setup_logging, get_logger
from src.infrastructure.logging.context import (
    get_correlation_id,
    set_correlation_id,
    generate_correlation_id
)

__all__ = [
    "setup_logging",
    "get_logger",
    "get_correlation_id",
    "set_correlation_id",
    "generate_correlation_id"
]
