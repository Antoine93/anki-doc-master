# Basic : Formules Mathématiques

Génère des cartes Question/Réponse pour les formules mathématiques.

## Stratégies

- Question : "Quelle formule pour calculer X ?"
- Question : "Que représente cette formule : [formule] ?"
- Question sur les variables : "Dans [formule], que représente X ?"

## Format LaTeX Anki

Utiliser le format Anki dans les réponses :
- Inline : `[$]formule[/$]`
- Display : `[$$]formule[/$$]`

## Interdictions LaTeX

- **NE PAS** modifier la syntaxe LaTeX (`\frac` → `/` interdit)
- **NE PAS** créer de questions sur la syntaxe LaTeX elle-même
- **Préserver** la formule exactement comme dans le document source

## Structure attendue

Pour chaque carte:
- front: Question sur la formule
- back: Formule en LaTeX + explication brève
- tags: Liste de tags

## Format JSON

```json
{"cards": [{"front": "Quelle est la formule de sortie d'une machine de Moore ?", "back": "[$$]output = g(state)[/$$]\nLa sortie dépend uniquement de l'état courant via la fonction g.", "tags": ["formule", "Moore"]}]}
```
