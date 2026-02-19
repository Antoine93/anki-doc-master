# Format Anki : Cartes Cloze

Formate les cartes à trous pour l'import Anki.

## Format de sortie

```
#separator:;
#html:true
#notetype:Cloze
{{c1::TCP}} est un protocole de transport.
Le {{c1::discriminant}} est [$]\Delta = b^2-4ac[/$].
```

**Différences avec basic** :
- Header supplémentaire : `#notetype:Cloze`
- **Une seule colonne** (pas de Q;R)
- Le `;` dans le texte n'est PAS un problème

## Règles

- **Préserver** `{{c1::...}}` intact
- **Préserver** `{{c1::...::indice}}` intact
- **Une carte = une ligne**
- Pas de ligne vide
- Encodage UTF-8

## Préservation syntaxe cloze

### NE PAS modifier
```
{{c1::terme}}           → garder tel quel
{{c2::autre}}           → garder tel quel
{{c1::terme::indice}}   → garder tel quel
```

### Vérification
Compter les `{{c` en entrée = en sortie.

## Formatage HTML

Mêmes règles que basic :

### Code inline
```
{{c1::TCP}} → {{c1::<code>TCP</code>}} si approprié
```

### LaTeX
```
{{c1::formule}} avec [$]...[/$] → PRÉSERVER les deux syntaxes
```

**Attention** : Ne pas mélanger cloze et LaTeX dans le même trou de manière incorrecte.

✅ Correct :
```
[$$]{{c1::F}} = ma[/$$]
```

❌ Incorrect :
```
{{c1::[$]F[/$]}} = ma   ← délimiteurs LaTeX dans le trou
```

## Structure attendue

Pour chaque carte :
- text: Texte complet avec syntaxe cloze

## Format JSON

```json
{"cards": [{"text": "{{c1::TCP}} est un protocole de la couche transport."}]}
```
