# Basic : Vocabulaire

Génère des cartes Question/Réponse **inversées** pour le glossaire de termes techniques.

## Format inversé obligatoire

- **Question** = La définition du terme
- **Réponse** = Le terme lui-même

Ce format force le rappel actif du terme à partir de sa signification.

## Stratégies

- Question : "[définition complète]" → Réponse : "[terme]"
- Question : "Identifiant numérique unique d'un processus" → Réponse : "PID (Process ID)"
- Pour les acronymes : inclure la forme développée dans la réponse

## Structure attendue

Pour chaque carte:
- front: Définition du terme (question)
- back: Terme ou acronyme (réponse)
- tags: Liste de tags (domaine, catégorie)

## Format JSON

```json
{"cards": [{"front": "Machine à états finis dont la sortie dépend uniquement de l'état courant.", "back": "Machine de Moore (FSM Moore)", "tags": ["FSM", "vocabulaire"]}]}
```
