# CONTEXTE CANONIQUE EZSCORE — décisions et état GitHub, 27 octobre 2026

**Objet** : référence durable pour reprendre le chantier après perte éventuelle du résumé mémoire ChatGPT. Le contenu n'est pas un substitut à la lecture des sources en vigueur : consulter les branches, AGENTS.md, issues, contrats, rapports et historiques **avant** chaque modification.

## 1. Décisions explicites et récentes du mainteneur — priorité haute

- Périmètre opérationnel **une seule machine MAIN**. Ne pas réintroduire des nœuds distants retirés du périmètre, ni la stack Docker abandonnée.
- **Toutes les tâches planifiées Windows de l'écosystème ont été supprimées volontairement**. Ne jamais en installer, proposer ou réactiver. Éviter les fenêtres PowerShell enfants et la perte de focus.
- **Caddy est l'unique porte d'entrée HTTP/HTTPS**. **`php -S` interdit**, y compris derrière Caddy. Ne pas confondre Caddy frontal et conformité du backend.
- **Tout passe par des contrats REST** entre composants. Authentification, gestion d'erreurs, journalisation et provenance obligatoires. Ne pas construire de serveur concurrent.
- Chaque composant détient un seul contrat de cycle de vie (`start`, `stop`, `status`, éventuellement `restart`). **Orchestrator supervise et délègue** ; il ne doit ni recopier les procédures ni inventer de CLI parallèles.
- Refonte **de l'interface Web de l'Orchestrator en Symfony modulaire**, Twig, Monolog, Profiler DEV, sécurité et API REST ; ne pas réécrire les moteurs d'analyse scientifique à cette occasion. Nouvelle fonctionnalité = module clair, pas ajout de scripts ad hoc.
- **GPU : une sonde unique locale sur MAIN, portée par l'Orchestrator**, consommée par REST par LAB et Assistant ; décommissionner les sondes dupliquées seulement après bascule/test.
- Environnements décidés : Orchestrator DEV ; EZStudio DEV/PROD (maintenance comme état PROD) ; LAB DEV ; Assistant DEV, local MAIN. Le mapping aux noms de répertoires et aux applications actuelles doit être vérifié, pas supposé.
- Publication vers `EZStudio_Run_Reports` : à la fin d'événements métier réellement confirmés (analyse, expertise), rapport ciblé et expurgé, avec déduplication et reprise durable. **Aucun polling/reporting périodique**, aucune publication massive d'historique.
- **Hygiène obligatoire** : supprimer les doublons, scripts/CLI obsolètes et traces de livraison sans retirer les mécanismes vivants ; fichiers temporaires uniquement sous `H:\temp` ; pas de livraison morcelée.
- **Services actuellement arrêtés sur MAIN à la demande du mainteneur**. Ne rien démarrer ni déclencher les jobs #181, #182, #185 avant nouvelle instruction explicite et recette adaptée.

## 2. Frontières fonctionnelles (sources et décisions)

- Pipeline scientifique LAB : **PROFILE → STEMS → CHORDS/N → LYRICS**, modules réglables et **presets** déclaratifs. Ne pas réintroduire les anciennes dénominations d'ADN/chromosome.
- Les analyses, révisions et évaluations doivent conserver leur provenance, leur degré d'incertitude et la distinction entre constat, hypothèse et validation.
- L'Assistant ne peut jamais altérer directement les résultats scientifiques ni promouvoir un preset actif sans protocole validé.
- **Conflit à arbitrer** : `EZS_orchestrator/contracts/ASSISTANT_SCIENTIFIQUE_PRESETS_R1.md` (2026-10-21) autorise une expertise scientifique intermodules, alors que `EZStudioLab_assistant/AGENTS.md` impose explicitement une contre-expertise **des items musicaux seulement**, sans audit des moteurs. Aucun nouvel élargissement de mission avant clarification du contrat prioritaire.

## 3. Sources de vérité et états vérifiés sur GitHub durant cette reconstruction

| Dépôt | Branche lue | HEAD vérifié | VERSION |
| --- | --- | --- | --- |
| `EZS_orchestrator` | `master` | `8aa7dd754d2d7f545b7f4fd9fe13f832a7b80b7a` | `1.3a(24)` |
| `EZStudio_lab` | `main` | `55187e57b4a829462fd82209287cf5dfc01076c6` | `1.4a` |
| `EZStudioLab_assistant` | `assistant-main` | `d4c68efa19640fe8a5f9cc63974a0aa16bdcd4e1` | `1.6a(155)` |
| `MAESTRO_WORKSPACE` | `master` | `2fdfcf5a77d4ce2d2dbc59eebca57e3cbcba2050` | sans VERSION vérifiée |

Règles canoniques : `AGENTS.md`, `REPOSITORY_HYGIENE.md`, README-FIRST et contrats de dépôt ; issues/handoffs. SHA = état à la date de lecture, **jamais** une autorisation de supposer une branche inchangée plus tard. `EZScore`/PROD et son mapping exact doivent être réinspectés lorsque concernés.

## 4. Écarts techniques constatés — ne pas présenter comme livrés

- `EZS_orchestrator/server_manager/manager.py` démarre encore des backends avec `php -S` et possède ses propres procédures ; **non conforme**.
- `EZStudio_lab/scripts/start.ps1` délègue actuellement à ce `ServerManager` ; LAB hérite de la non-conformité.
- Assistant MAIN `scripts/main-native-web.ps1` emploie aussi `php -S` ; `main-native-caddy.ps1` fait le proxy mais ne corrige pas ce problème. Les scripts sont des prototypes, pas le cycle de vie cible.
- `EZS_orchestrator/assistant_supervision/main_supervisor.py` conserve une supervision Docker ; hors architecture retenue.
- `EZStudio_lab/src/Controller/GpuTelemetryController.php` et `EZStudioLab_assistant/src/Controller/GpuTelemetryController.php` exécutent deux sondes similaires. Centralisation GPU pas encore livrée.
- Nettoyage du circuit de rapports expérimental : Orchestrator commit `8aa7dd7` a retiré modules `reports_*` expérimentaux ; LAB commit `55187e5` a retiré outbox et export ciblé sans consommateur. Publication événementielle **non opérationnelle** ; préserver le publieur historique tant que dépendances non auditées.
- Symfony de l'Orchestrator : **décision cible, pas livraison V2 opérationnelle**. Ne pas prétendre qu'un backend FastCGI ou une UI a été validé.
- Les scripts de planification historiques encore présents dans Git ne signifient pas que des tâches Windows existent ; suppression des fichiers seulement après inventaire de références.

## 5. Discipline des livraisons

1. Lire GitHub transversal, versions, contrats, historique, issues ; clarifier les contradictions avant de coder.
2. Rechercher les fonctionnalités déjà disponibles ; **remplacer/déléguer au lieu d'ajouter**. Une seule modification cohérente à la fois, sans régression.
3. Modifier uniquement les fichiers durables nécessaires. Tests de contrat + contrôles non-régression ; ne jamais qualifier de « réussi » un test non exécuté.
4. Respecter la version canonique, commit multiligne conforme `[vVERSION] type(périmètre): ...`, mettre à jour handoff/issue ; laisser le mainteneur faire les pulls et validations Windows.
5. UTF-8 sans BOM pour les nouveaux fichiers, sources lisibles, aucune pollution de dépôt, aucun secret, audio, modèle ni rapport brut exporté.
6. Les changements d'architecture doivent **retirer** les chemins devenus obsolètes lors de la bascule vérifiée, pas les laisser croître en parallèle.
7. Aucun démarrage automatisé, publication, mutation d'instance ou déploiement en conséquence de la seule reconstruction de contexte.

## 6. Prochain chantier autorisé

**Premier lot V2** : établir la matrice REST + propriétaire des commandes `start/stop/status` + stratégie Caddy/serveur PHP compatible, puis créer *un seul module Symfony démontrable et testable* sans démarrage des services existants. Lister les CLI à éliminer après qualification, sans supprimer les chemins réellement utilisés. Relever explicitement l'incompatibilité entre le contrat transversal et le contrat Assistant avant modification métier.

## 7. Limite sur la mémoire ChatGPT

Ce document reconstruit les **faits et décisions consultables** et sert de source durable sur GitHub. Il **ne restaure pas automatiquement** un résumé mémoire effacé dans les paramètres ChatGPT. Une modification de la mémoire du compte se fait séparément via `Paramètres → Personnalisation → Résumé de mémoire → Gérer`.
