# Cartes Cloze (Texte à trous)

Ce type de carte utilise la syntaxe Anki cloze deletion.

## Syntaxe Anki

- `{{c1::texte masqué}}` : Premier trou (une carte générée)
- `{{c2::texte masqué}}` : Deuxième trou (carte séparée)
- `{{c1::texte masqué::indice}}` : Trou avec indice affiché

## Structure obligatoire

Chaque carte doit avoir :
- **text** : Phrase complète avec syntaxe cloze
- **tags** : Liste de tags pour la catégorisation

## Règles de formulation

### Texte (text)
- Phrase complète et grammaticalement correcte
- Le texte masqué doit être un élément clé (terme, valeur, concept)
- Utiliser plusieurs trous (c1, c2) pour les relations importantes

### Indices
- Ajouter un indice si le contexte est insuffisant
- Format : `{{c1::réponse::catégorie}}` ou `{{c1::réponse::nombre de mots}}`

## Format JSON attendu

```json
{
  "cards": [
    {
      "text": "Une {{c1::phrase}} avec {{c2::deux trous}} distincts.",
      "tags": ["tag1", "tag2"]
    }
  ]
}
```

## Stratégies de masquage

1. **Termes techniques** : Masquer le terme, garder la définition visible
2. **Valeurs/Formules** : Masquer la valeur numérique ou le résultat
3. **Relations** : Utiliser c1/c2 pour lier deux concepts
4. **Listes** : Masquer les éléments clés d'une énumération

## Critères de qualité

- Le contexte visible doit permettre de déduire la réponse
- Éviter de masquer trop de texte (max 5-7 mots par trou)
- Un trou = un concept atomique
