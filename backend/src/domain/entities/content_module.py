"""
Énumération des modules de contenu détectables par l'analyste.

Chaque module représente un type de contenu spécifique que l'analyste
peut identifier dans un document source.
"""
from enum import Enum


class ContentModule(str, Enum):
    """
    Modules de contenu disponibles pour l'analyse.

    L'analyste évalue la présence et la pertinence de chaque module
    dans le document source. Extensible via ajout de nouvelles valeurs.
    """
    THEMES = "themes"
    VOCABULARY = "vocabulary"
    IMAGES_LIST = "images_list"              # Liste des images avec pages
    IMAGES_DESCRIPTIONS = "images_descriptions"  # Descriptions textuelles
    TABLES = "tables"
    MATH_FORMULAS = "math_formulas"
    CODE = "code"

    @classmethod
    def all_modules(cls) -> list[str]:
        """Retourne la liste de tous les modules disponibles."""
        return [module.value for module in cls]

    @classmethod
    def get_description(cls, module: str) -> str:
        """Retourne la description d'un module."""
        descriptions = {
            "themes": "Thèmes et sous-thèmes du document",
            "vocabulary": "Termes techniques et définitions",
            "images_list": "Liste des images/schémas avec numéros de page",
            "images_descriptions": "Descriptions textuelles des images",
            "tables": "Tableaux de données",
            "math_formulas": "Formules et équations mathématiques",
            "code": "Blocs de code et exemples"
        }
        return descriptions.get(module, "Module inconnu")
