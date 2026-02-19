# Cloze : Liste des Images

Génère des cartes à trous référençant les images du document.

## Syntaxe Anki Cloze

- `{{c1::élément masqué}}`

## Stratégies

- Masquer ce que représente l'image
- Masquer le type de schéma

## Note

Ces cartes servent de référence. Les images devront être ajoutées manuellement.

## Structure attendue

Pour chaque carte:
- text: Description avec cloze + référence à l'image
- tags: Liste de tags

## Format JSON

```json
{"cards": [{"text": "La Figure 1 (p.5) représente un {{c1::diagramme de transition}} d'une {{c2::FSM Moore}}.", "tags": ["image", "FSM"]}]}
```
