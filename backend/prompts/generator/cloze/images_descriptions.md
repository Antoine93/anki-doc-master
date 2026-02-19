# Cloze : Descriptions des Images

Génère des cartes à trous basées sur les descriptions détaillées des images.

## Syntaxe Anki Cloze

- `{{c1::élément masqué}}`
- `{{c1::élément::indice}}`

## Stratégies

- Masquer les éléments clés d'un schéma
- Masquer les relations entre éléments visuels
- Masquer l'interprétation d'un diagramme

## Structure attendue

Pour chaque carte:
- text: Description avec éléments masqués
- tags: Liste de tags

## Format JSON

```json
{"cards": [{"text": "Le diagramme FSM contient {{c1::3::nombre}} états : {{c2::S0}} (initial), {{c3::S1}} et {{c4::S2}} (final).", "tags": ["FSM", "diagramme"]}]}
```
