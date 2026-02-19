# Optimisation Basic : Tableaux

Règles spécifiques pour optimiser les cartes Q/R issues de tableaux.

## Atomisation des tableaux

### Une ligne = une carte (ou plusieurs)

**Avant** :
```
Q: Donnez la table de vérité de la FSM
R: S0+0→S1, S0+1→S0, S1+0→S1, S1+1→S0
```

**Après** (4 cartes) :
```
Q: [FSM] État S0 + entrée 0 → quel état suivant ?
R: S1

Q: [FSM] État S0 + entrée 1 → quel état suivant ?
R: S0

Q: [FSM] État S1 + entrée 0 → quel état suivant ?
R: S1

Q: [FSM] État S1 + entrée 1 → quel état suivant ?
R: S0
```

### Comparaisons → cartes par critère

**Avant** :
```
Q: Différences entre Moore et Mealy ?
R: Moore: sortie=f(état), synchrone, stable. Mealy: sortie=f(état,entrée), asynchrone, réactif.
```

**Après** (3 cartes) :
```
Q: [Moore vs Mealy] De quoi dépend la sortie ?
R: Moore: état seul. Mealy: état + entrées.

Q: [Moore vs Mealy] Lequel est synchrone ?
R: Moore (sortie change uniquement sur front d'horloge)

Q: [Moore vs Mealy] Lequel réagit plus vite aux entrées ?
R: Mealy (sortie peut changer immédiatement)
```

## Références

Conserver les références au tableau source :
```
Q: [Table 2.1] Valeur de X quand Y=1 ?
R: ...
```
