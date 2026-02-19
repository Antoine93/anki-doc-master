# Optimisation : Cartes Cloze

Optimise les cartes à trous selon les règles SuperMemo.

## Préservation syntaxe

**OBLIGATOIRE** :
- Conserver `{{c1::`, `{{c2::`, etc. exactement
- Conserver les `}}` de fermeture
- Ne pas renuméroter les indices
- Ne pas convertir en carte basique

## Transformations autorisées

### 1. Contexte insuffisant

Si le trou est ambigu, enrichir le texte **autour** (pas dedans).

**Avant** :
```
{{c1::Moore}} est un type de FSM.
```

**Après** :
```
Une {{c1::machine de Moore}} est un type de FSM dont la sortie dépend uniquement de l'état.
```

### 2. Trop de trous (>3)

Diviser en plusieurs cartes, chacune avec 1-3 trous max.

**Avant** :
```
Le {{c1::pipeline}} MIPS a 5 étapes : {{c2::Fetch}}, {{c3::Decode}}, {{c4::Execute}}, {{c5::Memory}}, {{c6::Writeback}}.
```

**Après** (2 cartes) :
```
Le {{c1::pipeline}} MIPS commence par {{c2::Fetch}} puis {{c3::Decode}}.

Après Decode, le pipeline MIPS continue avec {{c1::Execute}}, {{c2::Memory}} et {{c3::Writeback}}.
```

### 3. Trou ambigu

Ajouter un indice contextuel avec la syntaxe `{{c1::réponse::indice}}`.

**Avant** :
```
{{c1::FSM}} signifie Finite State Machine.
```

**Après** :
```
{{c1::FSM::acronyme 3 lettres}} signifie Finite State Machine.
```

### 4. Anti-interférence (Règle 11)

Pour différencier des concepts similaires, ajouter du contexte distinctif.

**Avant** :
```
La sortie dépend de {{c1::l'état courant}}.
La sortie dépend de {{c1::l'état et des entrées}}.
```

**Après** :
```
[Moore] La sortie dépend de {{c1::l'état courant}} uniquement.
[Mealy] La sortie dépend de {{c1::l'état ET des entrées}}.
```

## Structure attendue

Pour chaque carte optimisée :
- text: Texte avec syntaxe cloze préservée
- original_id: Référence à la carte source (si division)
- tags: Liste de tags

## Format JSON

```json
{"cards": [{"text": "Une {{c1::machine de Moore}} est...", "original_id": "card-1", "tags": ["optimized"]}]}
```
