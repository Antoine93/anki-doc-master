# Basic : Thèmes

Génère des cartes Question/Réponse à partir des thèmes et concepts.

## Stratégies

- Question sur la définition d'un concept
- Question sur la relation entre concepts
- Question "Qu'est-ce que..." / "Quel est..."
- Question sur les caractéristiques d'un thème

## Structure attendue

Pour chaque carte:
- front: Question claire et précise
- back: Réponse concise (1-3 phrases max)
- tags: Liste de tags (thème, sous-thème)

## Format JSON

```json
{"cards": [{"front": "Qu'est-ce qu'une machine de Moore ?", "back": "Une machine à états finis dont la sortie dépend uniquement de l'état courant, pas des entrées.", "tags": ["FSM", "Moore"]}]}
```
