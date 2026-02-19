# Basic : Descriptions des Images

Génère des cartes Question/Réponse basées sur les descriptions détaillées des images.

## Stratégies

- Question sur les éléments clés d'un schéma
- Question sur l'interprétation d'un diagramme
- Question sur la valeur pédagogique de l'image

## Structure attendue

Pour chaque carte:
- front: Question sur le contenu visuel
- back: Réponse basée sur la description textuelle
- tags: Liste de tags

## Format JSON

```json
{"cards": [{"front": "Quels sont les 3 états représentés dans le diagramme FSM ?", "back": "S0 (état initial), S1 (état intermédiaire), S2 (état final). Les transitions sont indiquées par des flèches avec conditions booléennes.", "tags": ["FSM", "diagramme"]}]}
```
