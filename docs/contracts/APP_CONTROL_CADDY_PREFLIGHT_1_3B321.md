# v1.3b321 — correctif n°1 de 1.3b32

Sur MAIN, `app-control` répondait `APP_CONTROL_SHARED_CADDY_UNAVAILABLE` pour start/stop/restart alors que `caddy-dev.cmd status` répondait `CADDY_DEV_REUSED PID=28860`. Le contrôle utilisait `$LASTEXITCODE`, valeur persistante propre aux exécutables externes qui ne reflète pas le succès d'un appel PowerShell `& $CaddyCheck`. Le contrôle compare maintenant exclusivement la sortie de la commande de statut du Caddy partagé (une ligne et PID positif). Aucun autre processus, état de backend ou configuration Caddy n'est modifié. Le refus reste effectif si statut inconnu.

Tests MAIN requis : Parser PowerShell, contrat PHP, contrôle de statut, puis action ciblée. Les PID historiques sont observés et non codés en dur. L'interface de pilotage et PROD restent hors périmètre.
