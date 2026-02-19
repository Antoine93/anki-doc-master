# Basic : Tableaux

Génère des cartes Question/Réponse à partir des tableaux de données.

## Stratégies

- Question sur une valeur spécifique du tableau
- Question de comparaison entre lignes/colonnes
- Question sur la structure ou le sens du tableau

## Structure attendue

Pour chaque carte:
- front: Question ciblant une donnée ou relation
- back: Réponse extraite du tableau
- tags: Liste de tags

## Format JSON

```json
{"cards": [{"front": "Dans une FSM Moore, quelle est la sortie quand l'état est S0 ?", "back": "La sortie est 1 (selon la table de vérité)", "tags": ["FSM", "table-verite"]}]}
```
