# Cloze : Tableaux

Génère des cartes à trous à partir des tableaux de données.

## Syntaxe Anki Cloze

- `{{c1::valeur masquée}}`

## Stratégies

- Masquer une valeur : "Quand état = S0, sortie = {{c1::1}}"
- Masquer une cellule dans un contexte
- Créer une phrase résumant une ligne du tableau

## Structure attendue

Pour chaque carte:
- text: Phrase décrivant une donnée du tableau avec cloze
- tags: Liste de tags

## Format JSON

```json
{"cards": [{"text": "Table FSM : État {{c1::S0}} + Input {{c2::0}} → Sortie {{c3::1}}", "tags": ["FSM", "table-verite"]}]}
```
