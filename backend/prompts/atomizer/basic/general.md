# Optimisation : Cartes Basic (Q/R)

Optimise les cartes Question/Réponse selon les règles SuperMemo.

## Transformations autorisées

### 1. Atomisation (Règle 4)

**Avant** :
```
Q: Quelles sont les caractéristiques d'une machine de Moore ?
R: La sortie dépend uniquement de l'état courant, elle est synchrone, et plus stable que Mealy.
```

**Après** (3 cartes) :
```
Q: De quoi dépend la sortie d'une machine de Moore ?
R: Uniquement de l'état courant.

Q: Une machine de Moore est-elle synchrone ou asynchrone ?
R: Synchrone.

Q: Entre Moore et Mealy, laquelle est plus stable ?
R: Moore.
```

### 2. Élimination des listes (Règle 9-10)

**Avant** :
```
Q: Citez les 5 étapes du pipeline MIPS.
R: Fetch, Decode, Execute, Memory, Writeback.
```

**Après** (5 cartes) :
```
Q: Quelle est la 1ère étape du pipeline MIPS ?
R: Fetch (récupération instruction).

Q: Quelle étape suit Fetch dans le pipeline MIPS ?
R: Decode.
...
```

### 3. Simplification (Règle 12/16)

**Avant** :
```
Q: Pouvez-vous expliquer ce qu'est un processus dans le contexte des systèmes d'exploitation ?
R: Un processus est essentiellement un programme qui est actuellement en cours d'exécution.
```

**Après** :
```
Q: Qu'est-ce qu'un processus ?
R: Un programme en cours d'exécution.
```

### 4. Anti-interférence (Règle 11)

Si deux cartes similaires risquent de créer de la confusion :
- Ajouter un **contexte différenciateur** dans la question
- Utiliser des indices spécifiques

**Exemple** :
```
Q: [Moore] De quoi dépend la sortie ?
R: De l'état courant uniquement.

Q: [Mealy] De quoi dépend la sortie ?
R: De l'état courant ET des entrées.
```

## Structure attendue

Pour chaque carte optimisée :
- front: Question simplifiée
- back: Réponse atomique (<100 caractères)
- original_id: Référence à la carte source (si division)
- tags: Liste de tags

## Format JSON

```json
{"cards": [{"front": "...", "back": "...", "original_id": "card-1", "tags": ["optimized"]}]}
```
