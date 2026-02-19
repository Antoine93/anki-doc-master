# Cloze : Code

Génère des cartes à trous pour les blocs de code.

## Syntaxe Anki Cloze

- `{{c1::code masqué}}` - premier trou

## Stratégies

- Masquer un mot-clé : `{{c1::process}}(clk)`
- Masquer une condition : `if {{c1::rising_edge}}(clk) then`
- Masquer une instruction : `{{c1::state <= next_state;}}`
- Masquer le nom d'une fonction/variable

## Structure attendue

Pour chaque carte:
- text: Code avec syntaxe cloze
- tags: Liste de tags (langage, concept)

## Format JSON

```json
{"cards": [{"text": "```vhdl\n{{c1::process}}(clk)\nbegin\n  if {{c2::rising_edge}}(clk) then\n    state <= {{c3::next_state}};\n  end if;\nend process;\n```", "tags": ["VHDL", "process"]}]}
```
