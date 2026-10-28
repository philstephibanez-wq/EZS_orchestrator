# PowerShell consolidation — v4.2b15

Décision mainteneur : exactement deux fichiers PS1 suivis, `scripts/start.ps1` et `scripts/stop.ps1`.

Les routines du cycle Orchestrator, LAB/Assistant et PROD sont incorporées dans les deux points d'entrée, pour préserver leurs mécanismes Windows d'attestation PID/port/heure, locks, états et conservation du Caddy partagé sans les réécrire en PHP non validé. Cette duplication est intentionnelle et transitoire ; une future refactorisation PHP devra prouver sa parité avant bascule.

Commandes existantes : `start.ps1` / `stop.ps1`. L'option `-RefreshDevApps` est maintenue. Actions PROD auparavant exécutées via `prod_lifecycle.ps1 -Action ...` disponibles via `start.ps1 -ProdAction start|status|normal|repair-fastcgi` ou `stop.ps1 -ProdAction stop|status|maintenance`. Ces actions PROD n'ont pas été validées sur MAIN dans ce commit : ne les invoquer qu'avec recette et autorisation de production.

Le script ponctuel Caddy de cutover v2.b9/v2.b10 est supprimé, mais sa trace et ses contrats restent dans Git. Les tests statiques historiques portant directement sur les chemins supprimés ne constituent plus des tests applicables, voir contrat de consolidation ci-après.

**Gates live non exécutés** : PowerShell parser, tests unitaires PHP, START/STOP MAIN, redémarrages contrôlés, Caddy DEV et maintenance PROD. Ne pas annoncer la stabilité finale sans cette recette. Aucune action MAIN/PROD n'est effectuée par le commit.

## Stabilisation de la série — 28/10/2026

Mainteneur : tests réels `scripts/stop.ps1` puis `scripts/start.ps1` confirmés **OK sur MAIN** après déploiement de 4.2b15. Contrôle PowerShell Parser : **SYNTAX_OK** sur les deux scripts. Contrat `OnlyStartStopPowershell42B15ContractTest.php` : **OK** sur MAIN. Inventaire Git : exactement deux scripts .ps1 suivis. Ces preuves autorisent la promotion canonique de la série en **4.2b STABLE** (retrait du compteur 15), sans modification du runtime.

Limites : opérations PROD autonomes via `-ProdAction` et cycle indépendant IA/chat non recettés par les tests de stabilisation ; ils restent hors déclaration de stabilité. Ports historiques 18713/18720 inactifs ; backend PHP Assistant 8713 présent ; sujet IA/chat sous responsabilité du composant Assistant et non attribué à un défaut de cycle START/STOP. Ne pas confondre cette stabilisation avec la clôture de toute la migration Symfony de l'issue #18.

Test statique de garde adapté pour accepter VERSION=4.2b tout en conservant le nom historique v4.2b15. Aucun test local exécuté par le commit de promotion ; l'état MAIN rapporté par le mainteneur est la preuve de validation.
