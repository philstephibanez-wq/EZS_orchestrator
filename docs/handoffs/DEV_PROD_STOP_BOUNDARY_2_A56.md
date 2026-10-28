# v2.a56 — correction critique de la séparation DEV / PROD

Le mainteneur a signalé que le STOP global v2.a55 arrêtait le gateway PHP PROD, coupant le site public. **Cette opération n'est pas conforme au contrat.**

Les deux points d'entrée `scripts/start.ps1` et `scripts/stop.ps1` sont rétablis en **DEV uniquement** et délèguent au lifecycle DEV déjà éprouvé, avec les vérifications d'identité historiques. Aucune opération sur PROD, sur le gateway PHP 8510/18515, sur les services 8501/8511/8512 ou sur les configurations de production n'est possible depuis ces deux scripts. Le gateway PHP **déjà en service reste actif**. Ne pas utiliser `scripts/prod_lifecycle.ps1`, qui repose encore sur un ancien gateway Python supprimé.

Les tests statiques précédents `GatewayPhpProdBootstrapContractTest.php`, `GlobalStartStopContractTest.php`, `GlobalDevStatusCaptureContractTest.php` et `GatewayProdRecipeIsolationContractTest.php` décrivaient des lanceurs monolithiques ou des branches gateway retirées ; ils sont remplacés par le contrat de non-interférence DEV/PROD. Le lancement du gateway PHP est aujourd'hui déjà effectif, mais son superviseur PHP permanent indépendant reste une exigence ouverte. Ne pas confondre source gateway PHP et procédure de reprise après reboot.

Recette MAIN : pull ; `php tests/DevProdLifecycleIsolationContractTest.php` ; **ne pas faire STOP** sans une fenêtre de test DEV. Pour une recette ultérieure, vérifier que `stop.ps1` n'affecte que DEV, et que les listeners PROD 8501/8510/8511/8512/18515 restent actifs et le site reste disponible. Aucune recette de STOP réelle n'a été exécutée pour cette version ; la séparation est prouvée par lecture de source uniquement.
