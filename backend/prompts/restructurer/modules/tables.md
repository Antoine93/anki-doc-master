# Module: Tableaux

Extrais tous les tableaux du document.

## Structure attendue

Pour chaque tableau:
- title: Titre/description
- headers: En-têtes colonnes
- rows: Données lignes
- page: Numéro de page

## Format JSON

```json
{"items": [{"title": "...", "headers": [...], "rows": [[...]], "page": 1}]}
```
