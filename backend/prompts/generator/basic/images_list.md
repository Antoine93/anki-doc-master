# Basic : Liste des Images

Génère des cartes Question/Réponse référençant les images du document.

## Stratégies

- Question : "Que représente la Figure X ?"
- Question : "Dans quel contexte utilise-t-on le schéma X ?"

## Note

Ces cartes servent de référence. Les images devront être ajoutées manuellement dans Anki.

## Structure attendue

Pour chaque carte:
- front: Question sur l'image
- back: Description + mention "[Voir Figure X, p.Y]"
- tags: Liste de tags

## Format JSON

```json
{"cards": [{"front": "Que représente la Figure 1 du cours ?", "back": "Le diagramme de transition d'une FSM Moore avec 3 états. [Voir Figure 1, p.5]", "tags": ["image", "FSM"]}]}
```
