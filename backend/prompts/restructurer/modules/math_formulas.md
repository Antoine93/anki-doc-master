# Module: Formules Mathématiques

Extrais toutes les formules et équations mathématiques importantes.

## Format LaTeX pour Anki

Utiliser le format Anki :
- Formule inline : `[$]formule[/$]`
- Formule display (bloc) : `[$$]formule[/$$]`

**RÈGLE CRITIQUE** : JAMAIS de texte sur la même ligne qu'une formule bloc `[$$]...[/$$]`

## Structure attendue

Pour chaque formule:
- formula: La formule en LaTeX format Anki (ex: `[$]E=mc^2[/$]`)
- description: Ce qu'elle représente
- variables: Dictionnaire variable → signification
- section: Section du document
- page: Numéro de page

## Format JSON

```json
{"items": [{"formula": "[$]output = g(state)[/$]", "description": "Sortie machine de Moore", "variables": {"output": "signal de sortie", "g": "fonction de sortie", "state": "état courant"}, "section": "1.1", "page": 3}]}
```
