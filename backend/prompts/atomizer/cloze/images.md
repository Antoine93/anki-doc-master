# Optimisation Cloze : Images

Règles spécifiques pour optimiser les cartes cloze référençant des images.

## Préservation des références

**TOUJOURS** conserver les références aux figures intactes (hors des trous) :
```
Le diagramme montre {{c1::3}} états. [Voir Figure 1]
```

❌ **Interdit** :
```
{{c1::[Voir Figure 1]}}  ← ne pas masquer les références
```

## Atomisation

### Description multi-éléments

**Avant** :
```
La Figure 1 montre {{c1::3 états}}, {{c2::des transitions fléchées}} et {{c3::des conditions booléennes}}. [Voir Figure 1, p.5]
```

**Après** (3 cartes) :
```
La Figure 1 montre {{c1::3::nombre}} états. [Voir Figure 1, p.5]

Dans la Figure 1, les transitions sont représentées par {{c1::des flèches}}. [Voir Figure 1, p.5]

Sur les flèches de la Figure 1, on trouve {{c1::les conditions booléennes}}. [Voir Figure 1, p.5]
```

## Schémas à compléter mentalement

Pour les cartes qui demandent de "visualiser" un schéma :

```
[Figure 1 - FSM] L'état {{c1::S0}} est connecté à {{c2::S1}} par la condition {{c3::input=1}}. [Voir Figure 1]
```

Ajouter un indice si ambigu :
```
L'état initial est {{c1::S0::cercle avec flèche entrante}}. [Voir Figure 1]
```
