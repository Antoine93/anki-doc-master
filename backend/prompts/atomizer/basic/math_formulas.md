# Optimisation Basic : Formules Mathématiques

Règles spécifiques pour optimiser les cartes Q/R contenant du LaTeX.

## Préservation LaTeX absolue

- **NE JAMAIS** modifier `[$]`, `[/$]`, `[$$]`, `[/$$]`
- **NE JAMAIS** modifier le contenu entre délimiteurs
- **NE JAMAIS** simplifier la syntaxe (`\frac` → `/` interdit)

## Atomisation des formules

### Formule multi-concepts → plusieurs cartes

**Avant** :
```
Q: Quelles sont les formules d'une FSM ?
R: Moore : [$$]output = g(state)[/$$], Mealy : [$$]output = h(state, input)[/$$]
```

**Après** (2 cartes) :
```
Q: Quelle est la formule de sortie d'une machine de Moore ?
R: [$$]output = g(state)[/$$]

Q: Quelle est la formule de sortie d'une machine de Mealy ?
R: [$$]output = h(state, input)[/$$]
```

### Variables multiples → une carte par variable

**Avant** :
```
Q: Que représentent les variables dans [$$]F = ma[/$$] ?
R: F = force, m = masse, a = accélération
```

**Après** (3 cartes) :
```
Q: Dans [$$]F = ma[/$$], que représente F ?
R: La force (en Newtons)

Q: Dans [$$]F = ma[/$$], que représente m ?
R: La masse (en kg)

Q: Dans [$$]F = ma[/$$], que représente a ?
R: L'accélération (en m/s²)
```

## Validation

Avant de finaliser, vérifier :
- Nombre de délimiteurs `[$]` en entrée = en sortie
- Contenu LaTeX identique caractère par caractère
