# 4.2c51 — Retablissement strict du contrat 2 Caddy sur MAIN

## Invariant
Un seul processus Caddy DEV partagé (Orchestrator, EZScore DEV, LAB, Assistant) et un seul processus Caddy PROD (public 8501, Gateway HTTP 8510, facade Symfony interne 8511). Aucun Caddy par frontend/backend. Les backends PHP FastCGI conservent leurs processus dédiés.

## Correction du code
- Nouveau `config/caddy/Caddyfile.prod-unified` combine les trois sites sans changer les chemins, ports, controles media ou frontal Cloudflare.
- `scripts/start.ps1` et `scripts/stop.ps1` lancent, en schema `ezs.prod.php.v2`, uniquement PHP-CGI 8512, PHP-CGI Gateway 18515 et Caddy PROD unifie.
- Verification des proprietaires des trois ports HTTP et des PIDs; protection par maintenance; rollback uniquement des processus lances et identifies.
- Schema existant `ezs.prod.php.v1` (trois Caddy PROD) reste lisible et stoppable par l'action PROD stop. Aucune adoption, destruction ou transformation implicite des PIDs existants. Un START refuse explicitement v1 actif, meme sain.
- Deux scripts START/STOP restent les points d'entree. Les composants DEV/LAB/Assistant ne sont pas modifies. La queue de jobs ne change pas.

## Recette MAIN (NON EXECUTEE par le developpeur)
1. Recuperer la publication dans l'arbre local propre : `git pull --ff-only origin master`, confirmer VERSION 4.2c51.
2. `php tests/ProdPhpOnly42C48ContractTest.php`; `php tests/ProdFastcgiDiagnostic42C50ContractTest.php`; `php tests/ProdTwoCaddy42C51ContractTest.php`.
3. Parse PowerShell des deux scripts : `[System.Management.Automation.Language.Parser]::ParseFile(...)`.
4. `H:\Caddy\caddy.exe validate --config H:\EZS_orchestrator\config\caddy\Caddyfile.prod-unified --adapter caddyfile`.
5. Mettre PROD en maintenance; appliquer uniquement `scripts/stop.ps1 -ProdAction stop` pour arreter l'ancien schema v1 apres confirmation de son ownership et du statut 503. Ne pas tuer des PIDs manuellement.
6. `scripts/start.ps1 -ProdAction start`, puis `scripts/start.ps1 -ProdAction status`; verificer 8501, 8510 et 8511 ecoutes par le MEME PID Caddy, routes maintenance/status et backend.
7. `scripts/start.ps1` (sans -ProdAction) pour retablir l'unique Caddy DEV mutualise, puis verifier 8790,8502,8852,8702,8712; observer la presence de exactement deux caddy.exe sur MAIN.
8. Recette SSO, media protege (sans fuite), queue LAB HTTP 8702 et affichage des jobs avant de sortir du mode maintenance.
9. Ne pas annoncer un succes global sans tous les controles ci-dessus. En cas de refus, ne pas relancer en boucle; consigner les marqueurs exacts.

## Notes importantes
- Une procedure de migration qui supprime/force le schema v1 est interdite. Le STOP confirme d'abord une maintenance HTTP 503.
- Ce correctif GitHub est **publie mais NON recette sur Windows MAIN**. Il ne retablit aucun service avant les operations explicites de MAIN.
- La cible finale des 2 Caddy n'est atteinte que si DEV ET PROD sont tous deux demarres et conformes.
- Ne pas changer les ports, le serveur PHP-only, le protocole Gateway v3 ni les contrats des jobs.
