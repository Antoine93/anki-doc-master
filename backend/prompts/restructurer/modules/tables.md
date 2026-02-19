# Module: Tableaux

Extrais tous les tableaux significatifs du document.

## Instructions

- Identifier chaque tableau avec ses données
- Préserver la structure colonnes/lignes
- Localiser précisément (section et page)

## Structure attendue

Pour chaque tableau:
- title: Titre ou description du tableau
- headers: Liste des en-têtes de colonnes
- rows: Données ligne par ligne (tableau 2D)
- section: Section du document
- page: Numéro de page
- columns_description: Description des colonnes (ex: "État, Input, Output")

## Format JSON

```json
{"items": [{"title": "Table de vérité FSM", "headers": ["État", "Input", "Output"], "rows": [["S0", "0", "1"], ["S1", "1", "0"]], "section": "1.2", "page": 6, "columns_description": "État courant, Entrée, Sortie"}]}
```
