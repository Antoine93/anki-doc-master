# Module: Descriptions des Images

Décris textuellement chaque image en détail pour permettre la création de cartes sans l'image originale.

## Instructions

- Description suffisamment détaillée pour comprendre l'image sans la voir
- Identifier les éléments clés (légendes, axes, flèches, etc.)
- Expliquer la valeur pédagogique (ce que l'image enseigne)

## Structure attendue

Pour chaque image:
- reference: Référence (ex: "Figure 1", "Schéma 2.3")
- detailed_description: Description complète et textuelle
- key_elements: Liste des éléments clés visibles
- educational_value: Ce que cette image permet d'apprendre
- section: Section du document
- page: Numéro de page

## Format JSON

```json
{"items": [{"reference": "Figure 1", "detailed_description": "Diagramme montrant les transitions entre états S0, S1 et S2 avec les conditions de transition sur chaque flèche", "key_elements": ["3 états circulaires", "flèches de transition", "conditions booléennes"], "educational_value": "Comprendre le fonctionnement d'une FSM Moore", "section": "1.2", "page": 5}]}
```
