# v1.3b23 — Orchestrator backend sans arrêt de Caddy DEV

Le lanceur `scripts/start.cmd` vérifie son singleton PHP puis utilise `scripts/caddy_dev_shared.ps1 start` pour réutiliser/démarrer le Caddy DEV préflight, sans redémarrage si déjà reconnu. `scripts/stop.cmd` arrête exclusivement PHP-CGI Orchestrator 8791. Il conserve les métadonnées permettant au gestionnaire partagé de reconnaître le PID Caddy issu de l'ancien V2. Les ports 8790 et 8852 restent servis même Orchestrator arrêté ; 8790 peut afficher 502. Aucun port public 8501/8502 n'est modifié.

Limite : le Caddyfile demeure celui du préflight et les scripts EZScore/LAB ne sont pas encore migrés. Tester sous MAIN `php web/tests/CaddyDevV2LifecycleContractTest.php`, puis `scripts/status.cmd`, `scripts/stop.cmd`, `scripts/caddy-dev.cmd status`, `scripts/start.cmd`, `scripts/status.cmd`. Le PID Caddy doit rester identique entre stop et start ; ne pas arrêter le proxy partagé.
