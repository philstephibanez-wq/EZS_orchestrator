# Préparation de la bascule 8790/8791 — v2.a10

## Preuve acquise
Sur MAIN, v2.a9 : PHP CGI 8891 et Caddy 8890 démarrés ; accueil correct avec GPU et quatre pavés ; `SYMFONY_ROOT_PREVIEW_HTTP_OK` exécuté. Cette preuve couvre le frontend root isolé uniquement, pas les actions historiques ni le lifecycle Windows de production.

## Configuration candidate
`config/caddy/Caddyfile.dev-root-candidate` reproduit le Caddyfile DEV actif, sauf commentaire d'identification et docroot Orchestrator `H:/EZS_orchestrator/public` au lieu de `web/public`. Les blocs EZScore 8502/8852 et leur authentification média restent byte-for-byte identiques. `config/caddy/Caddyfile.dev` est toujours actif et inchangé.

## Vérifications obligatoires avant toute activation
- `php tests/SymfonyRootCaddyCandidateContractTest.php` ; `caddy validate --config config/caddy/Caddyfile.dev-root-candidate --adapter caddyfile`.
- Sur MAIN, lire la commande et la configuration réelles des processus propriétaires des ports 8790 et 8791, et comparer avec la configuration active : ne pas supposer que le service utilise le fichier du dépôt.
- Contrôler l'environnement PHP CGI historique (root du processus, APP_ENV, variables nécessaires), les références persistantes `web/`, les callbacks et opérations qui seraient perdus.
- Inventorier toutes les routes/API historiques en usage (jobs, logs, actions, déploiements, Assistant, PROD). Tant qu'elles sont absentes au root, refuser le cutover ; le test preview accepte intentionnellement `jobs_migration_pending` 503.
- Prévoir fenêtre de maintenance, sauvegarde de la configuration active, propriété stricte des PID, non-régression EZScore, démarrage/arrêt sans console et rollback HTTP démontré. Ne jamais tuer un PID non vérifié ni retirer `web/` à cette étape.

## Statut
**Candidate publiée, aucun service activé.** Le lanceur racine `scripts/start.ps1` reste fail-closed. Toute activation ultérieure doit être un lot indépendant avec recette opérationnelle attestée, pas un simple changement de docroot. Le cas échéant maintenir 8890/8891 comme laboratoire uniquement.
