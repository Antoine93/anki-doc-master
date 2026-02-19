"""
Configuration centralisée du logging.

Fournit un formateur JSON structuré avec correlation_id
pour la traçabilité des requêtes de bout en bout.
"""
import logging
import logging.handlers
import json
from datetime import datetime
from pathlib import Path
from typing import Any

from src.infrastructure.logging.context import get_correlation_id


class JSONFormatter(logging.Formatter):
    """
    Formateur JSON pour logs structurés.

    Inclut automatiquement le correlation_id pour traçabilité.
    """

    def format(self, record: logging.LogRecord) -> str:
        """Formate un log en JSON structuré."""
        log_data = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "level": record.levelname,
            "correlation_id": get_correlation_id(),
            "layer": getattr(record, "layer", "unknown"),
            "module": record.name,
            "function": record.funcName,
            "line": record.lineno,
            "message": record.getMessage(),
        }

        # Ajouter les extras s'ils existent
        if hasattr(record, "extra_data"):
            log_data["extra"] = record.extra_data

        # Ajouter l'exception si présente
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)

        return json.dumps(log_data, ensure_ascii=False, default=str)


class SimpleFormatter(logging.Formatter):
    """
    Formateur simple pour la console en développement.

    Format: [LEVEL] layer | module:function:line - message
    """

    def format(self, record: logging.LogRecord) -> str:
        """Formate un log en texte simple."""
        layer = getattr(record, "layer", "unknown")
        correlation_id = get_correlation_id()
        cid_short = correlation_id[:8] if correlation_id else "--------"

        base = (
            f"[{record.levelname:7}] {cid_short} | {layer:10} | "
            f"{record.name}:{record.funcName}:{record.lineno} - {record.getMessage()}"
        )

        # Ajouter les extras s'ils existent (prompts, réponses, etc.)
        if hasattr(record, "extra_data") and record.extra_data:
            extras = record.extra_data
            extra_lines = []
            for key, value in extras.items():
                # Tronquer les valeurs très longues pour la console
                str_value = str(value)
                if len(str_value) > 500:
                    str_value = str_value[:500] + "... [tronqué]"
                extra_lines.append(f"    {key}: {str_value}")
            if extra_lines:
                base += "\n" + "\n".join(extra_lines)

        return base


def setup_logging(
    log_dir: str = "logs",
    level: int = logging.INFO,
    json_format: bool = False
) -> None:
    """
    Configure le logging centralisé de l'application.

    Args:
        log_dir: Répertoire pour les fichiers de logs
        level: Niveau de log minimum (défaut: INFO)
        json_format: True pour JSON, False pour format simple (défaut)
    """
    # Créer le répertoire de logs
    log_path = Path(log_dir)
    log_path.mkdir(exist_ok=True)

    # Choisir le formateur
    formatter = JSONFormatter() if json_format else SimpleFormatter()

    # Handler console
    console_handler = logging.StreamHandler()
    console_handler.setLevel(level)
    console_handler.setFormatter(formatter)

    # Handler fichier app.log (tous les logs)
    app_handler = logging.handlers.RotatingFileHandler(
        log_path / "app.log",
        maxBytes=10_000_000,  # 10 MB
        backupCount=5,
        encoding="utf-8"
    )
    app_handler.setLevel(level)
    app_handler.setFormatter(JSONFormatter())  # Toujours JSON en fichier

    # Handler fichier error.log (erreurs uniquement)
    error_handler = logging.handlers.RotatingFileHandler(
        log_path / "error.log",
        maxBytes=10_000_000,
        backupCount=5,
        encoding="utf-8"
    )
    error_handler.setLevel(logging.ERROR)
    error_handler.setFormatter(JSONFormatter())

    # Configuration du logger racine
    root_logger = logging.getLogger()
    root_logger.setLevel(level)

    # Nettoyer les handlers existants
    root_logger.handlers.clear()

    root_logger.addHandler(console_handler)
    root_logger.addHandler(app_handler)
    root_logger.addHandler(error_handler)

    # Réduire le bruit des bibliothèques tierces
    logging.getLogger("uvicorn").setLevel(logging.WARNING)
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)


def get_logger(name: str, layer: str) -> "LoggerWithLayer":
    """
    Obtient un logger avec contexte de couche.

    Args:
        name: Nom du module (utiliser __name__)
        layer: Couche architecturale (router, service, repository)

    Returns:
        Logger adapté avec contexte
    """
    logger = logging.getLogger(name)
    return LoggerWithLayer(logger, {"layer": layer})


class LoggerWithLayer(logging.LoggerAdapter):
    """Logger adapter qui ajoute la couche architecturale."""

    def process(self, msg: str, kwargs: dict) -> tuple[str, dict]:
        """Ajoute la couche au record."""
        kwargs.setdefault("extra", {})
        kwargs["extra"]["layer"] = self.extra.get("layer", "unknown")
        return msg, kwargs

    def with_extra(self, **extra_data: Any) -> "LoggerWithExtra":
        """Retourne un logger avec données supplémentaires."""
        return LoggerWithExtra(self.logger, self.extra, extra_data)


class LoggerWithExtra(logging.LoggerAdapter):
    """Logger adapter avec données extra."""

    def __init__(
        self,
        logger: logging.Logger,
        layer_extra: dict,
        extra_data: dict
    ) -> None:
        super().__init__(logger, layer_extra)
        self._extra_data = extra_data

    def process(self, msg: str, kwargs: dict) -> tuple[str, dict]:
        """Ajoute la couche et les extras au record."""
        kwargs.setdefault("extra", {})
        kwargs["extra"]["layer"] = self.extra.get("layer", "unknown")
        kwargs["extra"]["extra_data"] = self._extra_data
        return msg, kwargs
