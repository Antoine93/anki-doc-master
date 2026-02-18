"""
Entité Analysis représentant le résultat d'une analyse de document.

L'analyse détecte les modules de contenu présents dans un document PDF
et fournit la liste des modules à invoquer pour le restructurateur.
"""
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional

from src.domain.entities.content_module import ContentModule


@dataclass
class Analysis:
    """
    Entité représentant une analyse de document.

    Règles métier:
    - L'analysis_id doit être non vide (sauf si None pour création)
    - Le document_id doit être non vide
    - Les modules détectés doivent être valides (ContentModule)
    - La date d'analyse ne peut pas être dans le futur

    NOTE: analysis_id est l'identifiant unique de l'analyse.
    Il sert également de nom de dossier dans outputs/{document_id}/{analysis_id}/
    """
    analysis_id: Optional[str]
    document_id: str
    detected_modules: list[str] = field(default_factory=list)
    analyzed_at: datetime = field(default_factory=datetime.now)

    def __post_init__(self) -> None:
        """Validation automatique à la création."""
        self._validate()

    def _validate(self) -> None:
        """Valide les règles métier de l'analyse."""
        if not self.document_id or self.document_id.strip() == "":
            raise ValueError("Le document_id ne peut pas être vide")

        if self.analysis_id is not None and self.analysis_id.strip() == "":
            raise ValueError("L'analysis_id ne peut pas être une chaîne vide")

        # Valider que les modules détectés sont valides
        valid_modules = ContentModule.all_modules()
        invalid_modules = [m for m in self.detected_modules if m not in valid_modules]
        if invalid_modules:
            raise ValueError(
                f"Modules invalides détectés: {invalid_modules}. "
                f"Modules valides: {valid_modules}"
            )

        # Vérifier que la date n'est pas dans le futur (tolérance 1 minute)
        now = datetime.now()
        if self.analyzed_at > now:
            # Tolérance d'une minute pour les décalages d'horloge
            from datetime import timedelta
            if self.analyzed_at > now + timedelta(minutes=1):
                raise ValueError("La date d'analyse ne peut pas être dans le futur")

    @property
    def module_count(self) -> int:
        """Retourne le nombre de modules détectés."""
        return len(self.detected_modules)

    def has_module(self, module: str) -> bool:
        """Vérifie si un module spécifique a été détecté."""
        return module in self.detected_modules

    def has_images(self) -> bool:
        """Vérifie si le document contient des images."""
        return (
            ContentModule.IMAGES_LIST.value in self.detected_modules or
            ContentModule.IMAGES_DESCRIPTIONS.value in self.detected_modules
        )

    def has_technical_content(self) -> bool:
        """Vérifie si le document contient du contenu technique."""
        technical_modules = [
            ContentModule.CODE.value,
            ContentModule.MATH_FORMULAS.value,
            ContentModule.TABLES.value
        ]
        return any(m in self.detected_modules for m in technical_modules)

    def to_dict(self) -> dict:
        """
        Convertit l'entité en dictionnaire.

        IMPORTANT: Utilisé uniquement pour le retour vers les ports.
        Ne jamais exposer l'entité directement.
        """
        return {
            "analysis_id": self.analysis_id,
            "document_id": self.document_id,
            "detected_modules": self.detected_modules.copy(),
            "analyzed_at": self.analyzed_at.isoformat()
        }
