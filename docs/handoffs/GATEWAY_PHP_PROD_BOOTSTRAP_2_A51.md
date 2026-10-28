# v2.a51 — gateway PHP PROD permanent, bootstrap réel et indépendant

## Livré

- `config/caddy/Caddyfile.gateway-php-prod` écoute sur loopback 8510, délègue à `php-cgi.exe` FastCGI 18515, conserve la réécriture d'URI nécessaire au router PHP existant et n'utilise pas `php -S`.
- `scripts/start.ps1 -Target gateway` contrôle les dépendances, l'absence des listeners 8510/18515, valide Caddy, démarre PHP-CGI et Caddy détachés avec fenêtre cachée, contrôle les listeners/PID et le protocole, inscrit les PID dans `runtime/v2-prod/gateway-php.json` sous verrou. Caddy public 8501, interne 8511 et PHP 8512 sont préservés.
- `scripts/stop.ps1 -Target gateway` refuse l'arrêt tant que les deux PIDs ne correspondent pas aux images, signatures et listeners attendus. Il n'arrête **aucun autre composant**. Les commandes sans argument conservent l'ancien lifecycle DEV.

Ce lot **ne supprime pas** les autres scripts PS1, car la migration des cycles DEV/PROD complète n'est pas prouvée. Il ne met pas à jour le state ancien `runtime/v2-prod/processes.json` dont le PID Python mort reste historique ; le nouvel état du gateway PHP est distinct.

## Validation MAIN et activation volontaire

1. `php tests/GatewayPhpProdBootstrapContractTest.php`
2. `H:\Caddy\caddy.exe validate --config H:\EZS_orchestrator\config\caddy\Caddyfile.gateway-php-prod --adapter caddyfile`
3. Vérifier que le port 8510 n'est pas occupé. **Seulement ensuite** `powershell -ExecutionPolicy Bypass -File .\scripts\start.ps1 -Target gateway`.
4. `Invoke-WebRequest http://127.0.0.1:8510/__ezscore_gateway_status -UseBasicParsing` ; contrôler maintenance, flux réels, SSO/cookies et fichiers médias.

Aucun démarrage PROD ni recette Windows zéro flash n'a été effectué depuis GitHub. Les wrappers utilisent encore PowerShell pour le bootstrap physique ; cette exception est permise par le contrat temporaire mais n'est pas la cible ultime «seulement deux scripts». Il reste notamment le lifecycle PROD PS1, le lifecycle DEV PS1 et la migration d'état/rollback. Ne pas utiliser `prod_lifecycle.ps1 -Action stop` : il cible le vieux gateway Python.
