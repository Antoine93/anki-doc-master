# Optimisation Cloze : Tableaux

Règles spécifiques pour optimiser les cartes cloze issues de tableaux.

## Atomisation des lignes

### Une valeur masquée par carte

**Avant** :
```
Table FSM : État {{c1::S0}} + Input {{c2::0}} → Next {{c3::S1}} → Output {{c4::1}}
```

**Après** (2 cartes) :
```
[FSM] État S0 + Input 0 → État suivant : {{c1::S1}}

[FSM] État S0 + Input 0 → Sortie : {{c1::1}}
```

## Anti-interférence (Règle 11)

Pour les tables avec lignes similaires, ajouter des indices distinctifs :

**Avant** (confusion possible) :
```
État {{c1::S0}} + Input 0 → {{c2::S1}}
État {{c1::S1}} + Input 0 → {{c2::S1}}
```

**Après** :
```
[Depuis S0] Input 0 → état suivant : {{c1::S1}}
[Depuis S1] Input 0 → état suivant : {{c1::S1::reste identique}}
```

## Comparaisons

### Tableau comparatif → trous sur différences

**Avant** :
```
{{c1::Moore}} : sortie = f(état). {{c2::Mealy}} : sortie = f(état, entrée).
```

**Après** :
```
[Moore] La sortie dépend de {{c1::l'état seul}}.

[Mealy] La sortie dépend de {{c1::l'état ET des entrées}}.
```

## Références

Conserver les références :
```
[Table 2.1] Quand X=1, Y={{c1::valeur}}
```
