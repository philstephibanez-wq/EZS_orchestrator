# v1.3b20 — Préflight PHP FastCGI DEV sans toucher aux ports publics

Un **seul** Caddy DEV de test sert désormais Orchestrator sur 8790 et un aperçu EZScore DEV sur **8852** via PHP-CGI **8862**. Le site EZScore réel reste sur son port public réservé 8502, sans modification ; PROD reste exclusivement 8501. Ne jamais déplacer les callback Google OAuth et Cloudflare dans ce préflight.

Les routes `/media/*` et `/internal/media/*` sont explicitement refusées par Caddy sur l'aperçu, évitant de contourner le `forward_auth` historique. Ce préflight n'est pas une validation du SSO ou des médias.

Commandes nouvelles : `scripts\\dev-preview.cmd start|status|stop`. Script unique FastCGI PHP, PID et signature vérifiés, port exclusivement 8862 ; aucun arrêt par nom ou par port. Les commandes d'interface graphique demeurent désactivées tant que l'endpoint de contrôle et le test des médias/SSO n'ont pas été validés. Ne pas considérer le sandbox 8852 comme une migration complète.

Sur MAIN : arrêter V2 `scripts\\stop.cmd`, git pull, puis `php web/tests/DevFastCgiPreviewContractTest.php`, `H:\\Caddy\\caddy.exe validate --config H:\\EZS_orchestrator\\web\\config\\caddy\\Caddyfile.dev-preflight --adapter caddyfile`. `scripts\\start.cmd` réactive Caddy unique ; `scripts\\dev-preview.cmd start` lance PHP-CGI 8862. Tester `http://127.0.0.1:8852/fr/login` et vérifier qu'aucun fichier média n'est servi. Enfin `scripts\\dev-preview.cmd stop` et `scripts\\stop.cmd`. Ne pas démarrer la preview en cas d'autre propriétaire du port 8862. Tests Windows non exécutés au commit.
