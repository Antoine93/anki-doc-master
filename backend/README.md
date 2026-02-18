# anki-doc-master


But du projet

Nous construisons un pipeline modulaire de génération de cartes d'étude Anki capable de traiter des documents sources variés (PDF, Markdown,
code, etc.) sur n'importe quel sujet (programmation, mathématiques, biologie, finance, etc.).

Problème résolu

Le pipeline actuel souffre de plusieurs limitations :
- Prompts monolithiques : L'agent lit 300+ lignes de instructions même si 80% ne s'appliquent pas au document traité
- Pas de traçabilité : Fichiers texte sans possibilité de requêtes, rollback ou comparaison
- Couplage fort : Impossible d'ajouter un nouveau type de contenu sans modifier tout le système

Solution architecturale

1. Système décisionnel intelligent (cards-expert)

Un pré-traiteur analyse le document et recommande uniquement les modules pertinents. Un document de biologie n'invoquera pas les modules LaTeX   ou code.

2. Séparation des responsabilités

Chaque étape du pipeline est indépendante :
- Concepteur : Restructure et extrait (thèmes, vocabulaire, code, formules, tableaux, images)
- Générateur : Crée les cartes selon le format demandé
- Optimiseur : Applique les règles SuperMemo
- Exporteur : Produit les fichiers Anki

3. Modules injectables

Chaque étape charge uniquement les modules nécessaires :
concepteur-base.md + mod_code.md + mod_math.md
Au lieu de tout charger, économisant ~50% de tokens.

4. Format comme paramètre universel

Basique (Q/R) et Cloze (texte à trous) sont applicables à tout type de contenu :
/cards-generateur [uuid] --format=cloze --content=code
/cards-generateur [uuid] --format=basique --content=vocab

5. PostgreSQL pour la traçabilité

Chaque étape lit/écrit dans la BD, permettant :
- Suivi de A à Z
- Pipelines interruptibles et reprenables
- Comparaison de versions
- Ajout manuel de cartes
- Audit trail complet

Extensibilité

Ajouter un nouveau module = créer un fichier + l'enregistrer. Le reste du pipeline n'est pas affecté.
