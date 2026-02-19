# Module: Code

Extrais tous les blocs de code significatifs du document.

## Instructions

- Identifier chaque bloc de code avec son langage
- Préserver le code source exact
- Décrire ce que fait le code
- Localiser précisément (section et page)

## Structure attendue

Pour chaque bloc:
- language: Langage de programmation (python, vhdl, c, java, etc.)
- code: Code source complet
- description: Ce que fait le code
- concepts: Liste des concepts illustrés par ce code
- section: Section du document
- page: Numéro de page
- lines: Nombre approximatif de lignes

## Format JSON

```json
{"items": [{"language": "vhdl", "code": "process(clk)\nbegin\n  ...\nend process;", "description": "Process FSM avec case", "concepts": ["machine à états", "process synchrone"], "section": "1.2", "page": 5, "lines": 25}]}
```
