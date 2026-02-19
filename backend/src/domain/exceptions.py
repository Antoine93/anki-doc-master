"""
Exceptions métier du domaine.

Ces exceptions représentent les erreurs métier qui peuvent
survenir dans le pipeline. Elles sont converties en codes HTTP
dans les routers.
"""


class DomainError(Exception):
    """Classe de base pour toutes les exceptions du domaine."""
    pass


class DomainValidationError(DomainError):
    """Erreur de validation des règles métier. HTTP 400."""
    pass


class DocumentNotFoundError(DomainError):
    """Document introuvable. HTTP 404."""
    pass


class AnalysisNotFoundError(DomainError):
    """Analyse introuvable. HTTP 404."""
    pass


class AnalysisAlreadyExistsError(DomainError):
    """Analyse déjà existante. HTTP 409."""
    pass


class RestructurationNotFoundError(DomainError):
    """Restructuration introuvable. HTTP 404."""
    pass


class RestructurationAlreadyExistsError(DomainError):
    """Restructuration déjà existante. HTTP 409."""
    pass


class ModuleNotFoundError(DomainError):
    """Module de contenu introuvable. HTTP 404."""
    pass


class ItemNotFoundError(DomainError):
    """Item de module introuvable. HTTP 404."""
    pass


class AIError(DomainError):
    """Erreur lors de l'appel à l'IA. HTTP 502."""
    pass


class InvalidPdfError(DomainError):
    """Fichier PDF invalide ou corrompu. HTTP 422."""
    pass


class PromptNotFoundError(DomainError):
    """Prompt de spécialiste introuvable. HTTP 404."""
    pass


class GenerationNotFoundError(DomainError):
    """Génération de cartes introuvable. HTTP 404."""
    pass


class GenerationAlreadyExistsError(DomainError):
    """Génération de cartes déjà existante. HTTP 409."""
    pass


class CardNotFoundError(DomainError):
    """Carte introuvable. HTTP 404."""
    pass


class OptimizationNotFoundError(DomainError):
    """Optimisation de cartes introuvable. HTTP 404."""
    pass


class OptimizationAlreadyExistsError(DomainError):
    """Optimisation de cartes déjà existante. HTTP 409."""
    pass
