# Cloze : Thèmes

Génère des cartes à trous (cloze deletion) à partir des thèmes et concepts.

## Syntaxe Anki Cloze

- `{{c1::texte masqué}}` - premier trou
- `{{c2::texte masqué}}` - deuxième trou (révélé séparément)
- `{{c1::texte masqué::indice}}` - avec indice

## Stratégies

- Masquer le terme clé dans une définition
- Masquer la caractéristique principale d'un concept
- Créer des trous multiples pour les relations

## Structure attendue

Pour chaque carte:
- text: Phrase complète avec syntaxe cloze
- tags: Liste de tags

## Format JSON

```json
{"cards": [{"text": "Une {{c1::machine de Moore}} est une FSM dont la sortie dépend uniquement de {{c2::l'état courant}}.", "tags": ["FSM", "Moore"]}]}
```
