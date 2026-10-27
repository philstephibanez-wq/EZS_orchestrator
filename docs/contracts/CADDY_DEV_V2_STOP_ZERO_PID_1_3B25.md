# 1.3b25 — arrêt idempotent avec PHP PID 0

Un état `runtime/v2-dev/processes.json` peut conserver `php_pid=0` après arrêt du backend Orchestrator, pendant que Caddy DEV continue de tourner. `scripts/stop.cmd` ignore explicitement ce PID sentinelle et conserve le PID Caddy : exécutions répétées sans `Stop-Process` sur PID zéro. Aucun changement de ports, de routage, de runtime applicatif ou de PROD. Contrat statique `web/tests/CaddyDevStoppedPidContractTest.php`. Le comportement effectif sous Windows doit encore être testé sur MAIN.
