# Cloze : Vocabulaire

Génère des cartes à trous **inversées** pour le glossaire de termes techniques.

## Format inversé

Privilégier le masquage du **terme** pour forcer son rappel à partir de la définition.

## Syntaxe Anki Cloze

- `{{c1::texte masqué}}` - premier trou
- `{{c1::texte masqué::indice}}` - avec indice

## Stratégies (par ordre de priorité)

1. Masquer le terme : "Une {{c1::machine de Moore}} est une FSM dont la sortie dépend uniquement de l'état."
2. Masquer terme + forme développée : "{{c1::FSM}} signifie {{c2::Finite State Machine}}."
3. Pour définitions longues : masquer les éléments clés de la définition

## Structure attendue

Pour chaque carte:
- text: Phrase avec syntaxe cloze (terme masqué de préférence)
- tags: Liste de tags

## Format JSON

```json
{"cards": [{"text": "Une {{c1::machine de Moore}} est une FSM dont la sortie dépend uniquement de {{c2::l'état courant}}.", "tags": ["FSM", "vocabulaire"]}]}
```
