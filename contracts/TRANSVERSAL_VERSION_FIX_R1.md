# CONTRAT TRANSVERSAL — VERSION ET FIX

Applicable à EZS_orchestrator, EZStudio_lab, EZStudioLab_assistant, EZScore_dev et aux autres dépôts de la chaîne EZScore, sans supposer qu'ils partagent un même numéro de version.

Format canonique : `MAJEUR.MINEURlettre(N)`, par exemple `1.4a(0)`, `1.4a(1)`, `1.6a(2)`.
- `(0)` est la livraison initiale d'une version fonctionnelle.
- Chaque correctif livré incrémente `N` d'une unité dans le dépôt concerné.
- La prochaine évolution fonctionnelle change la version de base et repart à `(0)`.
- Tous les validateurs de version, écrans, scripts de déploiement, API de statut et tests doivent accepter le même format et afficher la valeur entière.
- Source, version installée, version du processus réellement actif, et version déclarée par l'orchestrateur sont des **faits différents**. Ne jamais déclarer déployé un commit simplement parce que GitHub a été mis à jour.
- Si plusieurs dépôts changent dans un livrable transversal : chaque dépôt conserve sa propre version mais ses correctifs, notes, commits et tests sont liés dans le même handoff.
- Toute livraison inclut commit descriptif, notes de release, issue/handoff, tag lorsque possible, prévol, déploiement ciblé, tests de non-régression et test fonctionnel de bout en bout.
- Aucune modification écrasée ou nettoyée automatiquement lors d'un échec `git status`. Lister les chemins exacts et arrêter avant mutation.
- Ne pas incrémenter aveuglément VERSION sans auditer d'abord son parseur : incident LAB `lab_version_invalid` lors de l'introduction de `(N)`.

Historique de référence 2026-10-22 : LAB `1.4a(1)`, Assistant `1.6a(2)` publié (à déployer), orchestrateur `1.2u` (format ancien, migration du validateur à traiter avant bump). Ceci n'implique pas la même valeur de VERSION sur tous les dépôts.
