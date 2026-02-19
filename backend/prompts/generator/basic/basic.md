# Cartes Basic (Question/Réponse)

Ce type de carte utilise le format classique recto/verso.

## Structure obligatoire

Chaque carte doit avoir :
- **front** : Question claire et précise (recto)
- **back** : Réponse concise, 1-3 phrases max (verso)
- **tags** : Liste de tags pour la catégorisation

## Règles de formulation

### Questions (front)
- Commencer par un mot interrogatif : "Qu'est-ce que", "Quel est", "Comment", "Pourquoi"
- Être précis et sans ambiguïté
- Une seule question par carte (atomicité)

### Réponses (back)
- Répondre directement à la question
- Éviter les phrases trop longues
- Inclure les éléments essentiels uniquement

## Format JSON attendu

```json
{
  "cards": [
    {
      "front": "Question précise ici ?",
      "back": "Réponse concise ici.",
      "tags": ["tag1", "tag2"]
    }
  ]
}
```

## Critères de qualité

- Chaque carte teste UN seul concept
- La réponse ne doit pas être devinable sans apprentissage
- Éviter les questions oui/non (préférer "Quel est..." à "Est-ce que...")
