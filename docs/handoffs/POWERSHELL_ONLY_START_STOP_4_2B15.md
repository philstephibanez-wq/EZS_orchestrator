# PowerShell consolidation — v4.2b15

Décision mainteneur : exactement deux fichiers PS1 suivis, `scripts/start.ps1` et `scripts/stop.ps1`.

Les routines du cycle Orchestrator, LAB/Assistant et PROD sont incorporées dans les deux points d'entrée, pour préserver leurs mécanismes Windows d'attestation PID/port/heure, locks, états et conservation du Caddy partagé sans les réécrire en PHP non validé. Cette duplication est intentionnelle et transitoire ; une future refactorisation PHP devra prouver sa parité avant bascule.

Commandes existantes : `start.ps1` / `stop.ps1`. L'option `-RefreshDevApps` est maintenue. Actions PROD auparavant exécutées via `prod_lifecycle.ps1 -Action ...` disponibles via `start.ps1 -ProdAction start|status|normal|repair-fastcgi` ou `stop.ps1 -ProdAction stop|status|maintenance`. Ces actions PROD n'ont pas été validées sur MAIN dans ce commit : ne les invoquer qu'avec recette et autorisation de production.

Le script ponctuel Caddy de cutover v2.b9/v2.b10 est supprimé, mais sa trace et ses contrats restent dans Git. Les tests statiques historiques portant directement sur les chemins supprimés ne constituent plus des tests applicables, voir contrat de consolidation ci-après.

**Gates live non exécutés** : PowerShell parser, tests unitaires PHP, START/STOP MAIN, redémarrages contrôlés, Caddy DEV et maintenance PROD. Ne pas annoncer la stabilité finale sans cette recette. Aucune action MAIN/PROD n'est effectuée par le commit.
