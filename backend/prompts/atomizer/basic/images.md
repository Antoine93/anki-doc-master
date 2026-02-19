# Optimisation Basic : Images

Règles spécifiques pour optimiser les cartes Q/R référençant des images.

## Préservation des références

**TOUJOURS** conserver les références aux figures :
- `[Voir Figure X]`
- `[Voir Figure X, p.Y]`
- `[Schéma 2.3]`

## Atomisation des descriptions

### Description multi-éléments → plusieurs cartes

**Avant** :
```
Q: Que montre la Figure 1 ?
R: Un diagramme FSM avec 3 états (S0, S1, S2), des transitions fléchées, et les conditions booléennes sur chaque flèche. [Voir Figure 1, p.5]
```

**Après** (3 cartes) :
```
Q: Combien d'états contient le diagramme FSM de la Figure 1 ?
R: 3 états : S0, S1, S2. [Voir Figure 1, p.5]

Q: Comment sont représentées les transitions dans la Figure 1 ?
R: Par des flèches entre les états. [Voir Figure 1, p.5]

Q: Que représentent les labels sur les flèches de la Figure 1 ?
R: Les conditions booléennes de transition. [Voir Figure 1, p.5]
```

## Carte "schéma à trous"

Si une carte demande de compléter un schéma mentalement :
- Garder la description textuelle suffisante
- Référencer explicitement l'image pour révision ultérieure

```
Q: Dans le diagramme FSM, quel état suit S0 si entrée=1 ?
R: S1. [Voir Figure 1, p.5]
```
