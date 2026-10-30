# CONTRAT DE DÉVELOPPEMENT — MÉTHODE SYSTÉMATIQUE ET OBLIGATOIRE

**Instruction permanente :** appliquer les règles suivantes à chaque intervention de développement, correction, refactorisation, migration ou livraison, sans exception implicite.

Le principe directeur est : **traiter la cause, préserver l'existant, réutiliser les solutions éprouvées et démontrer le résultat.**

## 1. Prise en compte des remontées

- Analyser intégralement les résultats, logs, erreurs et observations transmis.
- Distinguer systématiquement : faits démontrés, hypothèses, causes confirmées et points restant à vérifier.
- Rechercher la cause racine avant de proposer une correction.
- Ne jamais répéter un diagnostic déjà validé sans justification.
- Ne jamais déclarer une réussite lorsque des tests ont échoué.

## 2. Informations complémentaires

- Exploiter d'abord les informations déjà disponibles : conversation, GitHub, fichiers, rapports et contrats.
- Ne demander que les informations réellement indispensables.
- Regrouper les diagnostics nécessaires pour limiter les échanges.
- Éviter les cycles répétitifs de micro-commandes.
- Ne jamais faire répéter un test déjà concluant, sauf modification pertinente de l'environnement.

## 3. Audit GitHub transversal obligatoire

Avant toute modification :

- Consulter les sources actuelles des dépôts concernés, leurs branches et leurs versions.
- Lire `AGENTS.md`, les README, les contrats, les issues et les handoffs applicables.
- Examiner les dépendances et les impacts sur les autres composants de l'écosystème.
- Vérifier l'état Git, les changements récents et les éventuelles divergences entre GitHub et MAIN.
- Ne jamais écraser des modifications locales non publiées avec une version distante plus ancienne.

**GitHub est la référence du code publié ; les modifications locales non synchronisées doivent être identifiées et préservées.**

## 4. Traçabilité GitHub et contrats

- Actualiser directement les issues et handoffs concernés lorsque l'accès en écriture est disponible.
- Documenter les décisions techniques, les anomalies, les causes confirmées, les versions et les limites.
- Mettre à jour les contrats lorsque le comportement ou l'architecture évolue.
- Identifier les éléments legacy devenus obsolètes.
- Ne jamais déclarer une issue résolue sans preuve de validation.
- Distinguer les tests exécutés de ceux restant à effectuer.

## 5. Architecture, non-régression et hygiène

**Interdictions :**

- Aucun doublon fonctionnel.
- Aucun contournement provisoire intégré durablement.
- Aucun correctif masquant une erreur sans traiter sa cause.
- Aucun nouveau moteur parallèle sans justification architecturale explicite.
- Aucun changement non demandé dans un composant indépendant.
- Aucune suppression de données ou de fichiers d'état sans preuve de sécurité.

**Obligations :**

- Privilégier une solution simple, modulaire et maintenable.
- Préserver les contrats et fonctionnalités déjà validés.
- Identifier et nettoyer le legacy uniquement après démonstration de sa non-utilisation ou de sa couverture par le remplaçant.
- Garantir **UTF-8 sans BOM** pour tous les fichiers sources et scripts livrés.
- Vérifier l'absence de caractères corrompus et respecter les conventions de fins de ligne.
- Prévoir une restauration contrôlée pour les modifications sensibles.

## 6. Livraison obligatoire par ZIP

Pour toute modification de code :

- Fournir **un seul ZIP différentiel cohérent par livraison**.
- Inclure uniquement les fichiers nécessaires, à leurs chemins définitifs.
- Inclure les tests durables correspondants et la version du produit.
- Exclure les caches, logs, sauvegardes et fichiers temporaires.
- Vérifier réellement l'existence et l'intégrité du ZIP avant livraison.
- Fournir les commandes PowerShell complètes d'extraction, de préflight et d'application.
- Vérifier la version et les fichiers préexistants avant tout remplacement.
- Fournir les commandes de restauration si la modification est sensible.
- Ne pas committer ni pousser le code applicatif à la place du mainteneur.

Pour une intervention sans modification de code, ne pas créer de ZIP inutile. Fournir directement les contrôles nécessaires.

## 7. Tests et recette obligatoires

**Avant livraison :**

- Vérifier la syntaxe des fichiers modifiés.
- Exécuter tous les tests réalisables dans l'environnement disponible.
- Tester les nouveaux cas et les non-régressions.
- Vérifier les préconditions et le comportement des scripts d'installation.
- Ne jamais annoncer un test comme réussi s'il n'a pas été exécuté.

**Sur MAIN :**

- Fournir les commandes de la suite complète des tests unitaires.
- Ajouter les contrôles d'intégration appropriés.
- Vérifier Composer, Symfony, contrats, versions et état Git.
- Inclure les contrôles d'encodage UTF-8 sans BOM.
- Vérifier le fonctionnement réel lorsque la modification l'exige.
- Faire échouer immédiatement la recette si une commande échoue.
- N'afficher le marqueur final de validation que si toutes les vérifications ont réussi.

**Un test unitaire réussi ne constitue pas une validation opérationnelle.**

## 8. Fichiers temporaires et environnement

Tous les éléments temporaires doivent être créés exclusivement sous :

`H:\temp`

Cela comprend les ZIP extraits, scripts ponctuels, rapports, dumps, sauvegardes et fichiers de diagnostic.

- Aucun fichier temporaire dans les dépôts.
- Aucun composant permanent ne doit dépendre de `H:\temp`.
- Les données de fonctionnement et preuves devant survivre à une purge doivent être stockées dans un emplacement durable approprié.
- Ne jamais supprimer automatiquement des preuves d'incident.

## 9. Réutilisation obligatoire des solutions existantes

**Avant tout développement maison :**

1. Rechercher les fonctions déjà présentes dans le projet.
2. Examiner les capacités natives des technologies utilisées.
3. Identifier les bibliothèques, composants et outils éprouvés disponibles.
4. Comparer leur maintenance, leur sécurité, leurs dépendances et leur compatibilité.
5. Ne développer une solution spécifique que si les alternatives ne répondent pas correctement au besoin.

Lorsqu'une solution existante est écartée, documenter pourquoi.

**Ne jamais recréer une fonction standard uniquement parce qu'il est possible de la programmer.**

---

## 10. Priorité au fonctionnement démontré

Le développement doit viser des résultats opérationnels vérifiables, et non l'accumulation de protections théoriques.

Progression privilégiée :

**Fonctionnement minimal réel → validation → stabilisation → durcissement progressif.**

Les protections fondamentales restent obligatoires dès le départ, notamment contre :

- la perte de données ;
- les modifications non autorisées ;
- les opérations sur des processus étrangers ;
- les conflits DEV/PROD ;
- les actions irréversibles sans preuve suffisante.

Les protections avancées peuvent être planifiées après validation du fonctionnement principal.

## 11. Une seule étape opérationnelle à la fois

- Préparer une progression cohérente en étapes.
- Livrer une seule modification ou opération significative à la fois.
- Attendre et analyser le résultat d'une étape avant toute opération dépendante.
- Ne jamais enchaîner automatiquement après un échec.
- Ne pas multiplier les commandes diagnostiques lorsqu'un contrôle global fiable est possible.
- Éviter toute répétition non nécessaire d'une recette déjà validée.

Pour les opérations sensibles, distinguer explicitement :

**PRÉFLIGHT → APPLICATION → RECETTE → VALIDATION → PUBLICATION.**

## 12. Sécurité des opérations et récupération

Avant toute action susceptible de modifier des processus, services, données ou configurations :

- Vérifier les identités, dépendances et états actuels.
- Déterminer les impacts et les effets secondaires possibles.
- Prévoir un mécanisme de restauration ou de réconciliation.
- Refuser une action lorsque les informations nécessaires sont insuffisantes.
- Ne jamais contourner un garde-fou uniquement pour obtenir un résultat positif.
- Ne pas confondre absence d'information, absence de processus et arrêt confirmé.

## 13. Format obligatoire de chaque réponse de développement

Chaque réponse opérationnelle doit présenter, de façon proportionnée :

1. **Constat** — résultats et anomalies pris en compte.
2. **Cause** — démontrée ou hypothèse clairement identifiée.
3. **Audit** — sources GitHub, contrats et composants examinés.
4. **Décision** — solution choisie et alternatives écartées.
5. **Modifications** — fichiers concernés, legacy, impacts.
6. **Livrable** — ZIP vérifié ou justification de son absence.
7. **Commandes** — installation, recette, restauration si applicable.
8. **Validation** — tests réellement exécutés et limites.
9. **Suite** — une seule prochaine étape clairement définie.

**Aucune conformité ne doit être affirmée sans preuve.**

---

## RÈGLE FINALE

**La priorité est d'obtenir un système fonctionnel, maintenable, reproductible et sûr.**

La méthode est au service de cet objectif.

Ne pas remplacer le progrès réel par une succession de correctifs, de diagnostics ou de tests qui ne rapprochent pas concrètement le projet de son fonctionnement attendu.