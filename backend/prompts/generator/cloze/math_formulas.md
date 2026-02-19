# Cloze : Formules Mathématiques

Génère des cartes à trous pour les formules mathématiques.

## Syntaxe Anki Cloze

- `{{c1::texte masqué}}` dans le LaTeX

## Format LaTeX Anki

- Inline : `[$]formule[/$]`
- Display : `[$$]formule[/$$]`

## Interdictions LaTeX

- **NE PAS** modifier la syntaxe LaTeX (`\frac` → `/` interdit)
- **NE PAS** créer de trous sur la syntaxe LaTeX (masquer `\frac` interdit)
- **Préserver** la formule exactement, ne masquer que les variables/valeurs

## Stratégies

- Masquer une variable : `[$]output = {{c1::g}}(state)[/$]`
- Masquer le résultat : `[$]{{c1::output}} = g(state)[/$]`
- Masquer toute la formule : `{{c1::[$]output = g(state)[/$]}}`
- Masquer l'opération : `[$]next = f(state {{c1::,}} input)[/$]`

## Structure attendue

Pour chaque carte:
- text: Formule avec syntaxe cloze intégrée au LaTeX
- tags: Liste de tags

## Format JSON

```json
{"cards": [{"text": "Sortie Moore : [$$]{{c1::output}} = {{c2::g}}({{c3::state}})[/$$]", "tags": ["formule", "Moore"]}]}
```
