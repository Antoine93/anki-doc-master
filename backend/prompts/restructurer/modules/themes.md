# Module: Thèmes

Extrais tous les thèmes et sous-thèmes du document en arborescence hiérarchique.

## Convention de numérotation obligatoire

- **Thèmes** : numérotation simple (1., 2., 3.)
- **Sous-thèmes** : numérotation hiérarchique (1.1, 1.2, 2.1)
- **Concepts** : numérotation complète (1.1.1, 1.1.2, 1.2.1)

## Structure attendue

Pour chaque thème:
- number: Numéro hiérarchique (ex: "1", "1.1", "1.1.1")
- title: Titre du thème
- content: Contenu détaillé / définition
- subtopics: Sous-thèmes avec même structure (récursif)

## Format JSON

```json
{"items": [{"number": "1", "title": "...", "content": "...", "subtopics": [{"number": "1.1", "title": "...", "content": "...", "subtopics": [...]}]}]}
```
