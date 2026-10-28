# v2.b2 — démarrage des deux backends applicatifs DEV

Diagnostic MAIN confirmé : Caddy partagé PID 29972 possède déjà 8790/8502/8852 ; PHP Orchestrator 8791 actif ; ports 8602 et 8862 absents. `start.ps1` ne démarrait que l'Orchestrator : les pages EZScore DEV et preview étaient sans backend.

Implémentation : `scripts/start.ps1` conserve le lifecycle Orchestrator, puis démarre PHP-CGI `H:/PHP/php-8.5-x64/php-cgi.exe -b 127.0.0.1:8602` et `-b 127.0.0.1:8862`, APP_ENV=dev, APP_DEBUG=1, working dir H:/EZScore_dev. État propriétaire `runtime/v2-dev/app-backends.json` sous verrou indépendant, contrôle PID/chemin/argument/création/port. Pas d'adoption des listeners étrangers ; rollback limité aux enfants identifiés ; contrôle HTTP /fr/login via Caddy 8502 et 8852 avant OK. Aucun nouveau Caddy n'est lancé.

`scripts/stop.ps1` conserve la maintenance PROD vérifiée avant toute action, arrête les deux backends DEV uniquement avec identité forte et bloque sur présence de listener étranger ; termine par le stop Orchestrator DEV. Caddy PROD 8501/8510/8511/8512/18515 et gateway PHP ne sont jamais arrêtés. La maintenance PROD ne se désactive pas avec START.

Tests MAIN : `php tests/DevAppBackends2B2ContractTest.php`, puis `powershell -ExecutionPolicy Bypass -File .\scripts\start.ps1`. Attendre `EZS_DEV_APPS_READY_8502_8852`. Ensuite `Invoke-WebRequest http://127.0.0.1:8502/fr/login -UseBasicParsing` et idem pour 8852. Le mode preview ne certifie pas OAuth/médias. Les ports 8701/8702/8712 n'ont aucun contrat de lancement démontré et ne sont pas démarrés.

Attention : code non exécuté sur MAIN à la publication ; pas de garantie zéro flash Windows sans recette live. Les scripts PS de lifecycle historiques restent à migrer vers PHP ; réduction à deux seuls PS1 non encore atteinte.
