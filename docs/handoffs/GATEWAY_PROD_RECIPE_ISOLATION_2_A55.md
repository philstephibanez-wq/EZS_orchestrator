# v2.a55 — isolation du mode recette sur le gateway de production

## Incident observé sur MAIN

Après `start.ps1` : DEV reconnu sain, validation Caddy réussie ; `GET /__ezscore_gateway_status` sur 8510 renvoie JSON 503 `gateway_recipe_refused`, `server_port=8510`, `config_exists=true`, `script_matches=true`, `config_is_temp=true`. Ces propriétés montrent que l'environnement transmis au worker PHP contient encore `EZS_GATEWAY_RECIPE_CONFIG` pointant vers une configuration d'essai dans le répertoire temporaire. La validation de recette la refuse à juste titre sur 8510.

## Correction

- Lors du bootstrap prod : suppression explicite des variables héritées `EZS_GATEWAY_RECIPE_CONFIG` et `EZS_GATEWAY_RECIPE_MODE` avant de créer `php-cgi.exe`.
- Dans le router PHP : sur port réel 8510, forcer la configuration canonique `H:/EZScore/var/runtime/online-gateway.json` et ignorer tout éventuel override de recette ; la recette isolée sur 18514/18515 n'est pas changée.
- Contrat statique dédié. Aucun nettoyage de PID, aucun port ni config PROD déplacé automatiquement.

## Recette

`git pull --ff-only origin master` ; `php tests/GatewayProdRecipeIsolationContractTest.php` ; vérifier 8510 et 18515 libres ainsi que l'absence de `runtime/v2-prod/gateway-php.json` créé par une autre tentative, puis `powershell -ExecutionPolicy Bypass -File .\scripts\start.ps1`. Contrôler réponse statut et liste de listeners. Si l'occupation existe déjà, **ne pas tuer de processus manuellement** : transmettre les PID.

## Limites

La vraie compatibilité SSO, cookies, flux audio/médias, et zéro fenêtre de console Windows n'est toujours pas démontrée. Le lifecycle PROD historique contient encore une dépendance Python obsolète ; ne pas l'utiliser. La cible finale deux PS1 et lifecycle Symfony complet reste ouverte. Tests MAIN non exécutés au moment du commit.
