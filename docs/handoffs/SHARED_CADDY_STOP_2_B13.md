# v2.b13 — STOP du backend Orchestrator sans arrêt du Caddy DEV partagé

MAIN : `scripts/stop.ps1` a activé maintenance PROD, arrêté les deux backends EZScore DEV 8602/8862, puis refusé l'arrêt car backend LAB 8701 écoute. Erreur d'architecture : la procédure `v2_lifecycle.ps1 -Action stop` veut arrêter le Caddy DEV partagé au lieu du seul backend Orchestrator.

Correction : sous son verrou, attester que le Caddy partagé est propriétaire de 8790/8502/8852, arrêter exclusivement PHP FastCGI Orchestrator 8791, enregistrer `php_pid=0`, **préserver le PID Caddy et ses routes**. START restaure le seul backend Orchestrator lorsqu'il est arrêté, sans redémarrer Caddy. Refus en cas de processus étranger, PID divergent ou route Caddy non attestée. Aucun arrêt LAB/Assistant ; leurs backends restent propres à leurs répertoires et au cycle de vie dédié. PROD maintenance inchangée.

Contrôle MAIN : `git pull --ff-only origin master`, `php tests/SharedCaddyStop2B13ContractTest.php`, puis seulement si STOP toujours demandé `powershell -ExecutionPolicy Bypass -File .\scripts\v2_lifecycle.ps1 -Action stop` ; `Get-NetTCPConnection` pour confirmer Caddy 8702/8712 et LAB 8701/Assistant 8713 toujours en écoute ; `scripts/start.ps1` rétablit Orchestrator et applications DEV selon leurs cycles. NB stop.ps1 effectué avant mise à jour a déjà arrêté 8602 et 8862 et activé maintenance PROD : cet état n'est pas annulé automatiquement.

Validation MAIN non réalisée à publication. Aucune modification scientifique, LAB, Assistant, Caddy config ni PROD.
