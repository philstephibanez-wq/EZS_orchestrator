# v2.a54 — correction du démarrage global sur DEV déjà actif

Recette MAIN v2.a53 : les deux contrats PHP sont OK, mais `start.ps1` refuse `DEV_STALE_OR_PARTIAL_STATE` malgré le diagnostic `EZS_STATUS php_owned=True caddy_owned=True state_present=True`. Cause : `v2_lifecycle.ps1` émet ce diagnostic avec `Write-Host` sur le flux Information PowerShell 5, alors que `Out-String` capturait uniquement le flux standard. Le statut était visible dans la console mais la variable `$devStatus` restait vide.

Correctif : rediriger explicitement le flux 6 vers 1 avant `Out-String` (`6>&1`), sans réduire les protections d'identité ni modifier les scripts DEV/PROD. Test de non-régression statique ajouté. Aucun processus ni port modifié par la publication.

Recette MAIN : `git pull --ff-only origin master`, `php tests/GlobalDevStatusCaptureContractTest.php`, puis `powershell -ExecutionPolicy Bypass -File .\scripts\start.ps1`. Attendu : `EZS_GLOBAL_START_DEV_ALREADY_READY`, puis tentative de démarrage ou de réutilisation du gateway PHP 8510. Si erreur, transmettre la sortie intégrale. Le démarrage réel de la passerelle et la parité SSO/médias restent non certifiés.
