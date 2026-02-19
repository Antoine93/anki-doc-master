# Format Anki : Cartes Basic (Q/R)

Formate les cartes Question/Réponse pour l'import Anki.

## Format de sortie

```
#separator:;
#html:true
Question1;Réponse1
Question2;Réponse2
```

**Règles** :
- Une carte = une ligne
- Question et réponse séparées par `;`
- Pas de ligne vide
- Encodage UTF-8

## Gestion du point-virgule

### Point-virgule dans le texte
Si `;` apparaît dans la question OU la réponse → entourer de guillemets.

**Exemple** :
```
Q: Que signifie ; ?
R: Point-virgule

→ "Que signifie ; ?";"Point-virgule"
```

### Guillemets + Point-virgule
Si `;` ET `"` dans le même champ → guillemets + doubler les guillemets internes.

**Exemple** :
```
Q: Qu'est-ce que ";" ?
R: Un séparateur

→ "Qu'est-ce que "";""?";"Un séparateur"
```

## Formatage HTML

### Code inline
```
Terme technique → <code>terme</code>
```

### Bloc de code
```
```python
code
```
→ <pre>code (échappé)</pre>
```

### Listes
```
- Item 1
- Item 2

→ Item 1<br>Item 2
```

## Structure attendue

Pour chaque carte :
- question: Question formatée HTML
- answer: Réponse formatée HTML

## Format JSON

```json
{"cards": [{"question": "Qu'est-ce qu'un processus ?", "answer": "Un programme en cours d'exécution."}]}
```
