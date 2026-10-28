# v2.b3 — correctif de paramètre PowerShell réservé

La recette MAIN v2.b2 a échoué sur `WaitOwned` parce que le paramètre `$pid` entre en conflit (sans distinction de casse) avec la variable automatique PowerShell `$PID`, constante/lecture seule. `stop.ps1` contenait le même défaut latent dans la fonction `Owned`.

Correction : les deux paramètres deviennent `$processId` et les références correspondantes sont réécrites. Aucun changement de topologie, des ports, des configurations ou de PROD. Le rollback local du lanceur précédent a tenté d'arrêter les enfants qu'il avait créés, sans garantie de leur disparition : ne pas forcer un start si 8602 ou 8862 sont encore occupés.

Validation MAIN : `git pull --ff-only origin master`, `php tests/DevPowerShellPidParameter2B3ContractTest.php`, puis contrôle de `Get-NetTCPConnection -LocalPort 8602,8862 -State Listen -ErrorAction SilentlyContinue` et `Test-Path .\runtime\v2-dev\app-backends.json`. Si état absent et listeners libres, `powershell -ExecutionPolicy Bypass -File .\scripts\start.ps1`. Si un port est occupé, ne pas tuer un PID inconnu. Aucune exécution MAIN de ce correctif au moment du commit.

STOP continue à demander et vérifier la maintenance PROD avant arrêt DEV. La réduction à deux seuls scripts PowerShell reste ouverte.
