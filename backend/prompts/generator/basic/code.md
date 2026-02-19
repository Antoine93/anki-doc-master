# Basic : Code

Génère des cartes Question/Réponse pour les blocs de code.

## Stratégies

- Question : "Que fait ce code ?" → explication
- Question : "Comment implémenter X en [langage] ?" → code
- Question sur un concept illustré par le code

## Structure attendue

Pour chaque carte:
- front: Question (peut inclure un snippet de code)
- back: Réponse avec code ou explication
- tags: Liste de tags (langage, concept)

## Format JSON

```json
{"cards": [{"front": "Comment déclarer un process synchrone en VHDL ?", "back": "```vhdl\nprocess(clk)\nbegin\n  if rising_edge(clk) then\n    -- logique\n  end if;\nend process;\n```", "tags": ["VHDL", "process", "synchrone"]}]}
```
