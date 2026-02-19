# Optimisation Cloze : Formules Mathématiques

Règles spécifiques pour optimiser les cartes cloze contenant du LaTeX.

## Double préservation

### LaTeX
- **NE JAMAIS** modifier `[$]`, `[/$]`, `[$$]`, `[/$$]`
- **NE JAMAIS** modifier le contenu entre délimiteurs

### Syntaxe Cloze
- **NE PAS** mettre un trou sur un délimiteur LaTeX
- **NE PAS** masquer `\frac`, `\sum`, etc. (syntaxe, pas contenu)
- **UNIQUEMENT** masquer les variables, valeurs, résultats

## Trous autorisés dans LaTeX

✅ **Correct** :
```
[$$]{{c1::F}} = ma[/$$]
[$$]E = {{c1::mc^2}}[/$$]
[$$]\frac{{{c1::a}}}{b} = c[/$$]
```

❌ **Interdit** :
```
{{c1::[$]}}F = ma[/$]        ← masque délimiteur
[$$]{{c1::\frac}}{a}{b}[/$$] ← masque syntaxe LaTeX
```

## Atomisation

### Formule avec trop de trous (>3)

**Avant** :
```
[$$]{{c1::F}} = {{c2::m}} \cdot {{c3::a}}[/$$] où {{c4::F}}=force, {{c5::m}}=masse, {{c6::a}}=accélération
```

**Après** (2 cartes) :
```
[$$]{{c1::F}} = {{c2::m}} \cdot {{c3::a}}[/$$]

Dans F=ma : {{c1::F}}=force, {{c2::m}}=masse, {{c3::a}}=accélération.
```

## Validation

- Compter délimiteurs LaTeX : entrée = sortie
- Vérifier que les trous sont DANS le LaTeX ou HORS, jamais à cheval
