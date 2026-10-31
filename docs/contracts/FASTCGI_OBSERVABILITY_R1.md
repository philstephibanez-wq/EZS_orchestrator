# 4.2c75 — Mesures et inventaire FastCGI

## Périmètre

- `ezs:services tick`: durées par groupe et totale en millisecondes (observabilité ; aucune attente ajoutée).
- `ezs:services diagnostics`: inventaire PHP-CGI local, classification `ACTIVE`, `RESIDUAL`, `UNVERIFIED`, ports écoutés, sans commandes complètes ni secrets.
- `ProdOperationsController`: temps séparés config/gateway/caddy/backend/total, sans divulgation de jeton dans le diagnostic.
- Twig PROD: dernière mesure, délai navigateur, état actualisé ou obsolète, code erreur. Aucun changement du comportement POST/CSRF.
- Réutiliser la même observation WMI/TCP à l'intérieur d'un groupe FastCGI lorsque tous les processus sont déjà sains ; réobserver avant toute mutation.

## Limites et protection

La reconnaissance d'un FastCGI résiduel requiert exécutable ET commande correspondant exactement à la spécification. L'inventaire ne donne jamais le droit de tuer un processus étranger ou uniquement apparenté à PHP. Le nettoyage existant de 4.2c73 reste inchangé pour les candidats attestés. Les résidus non attribuables sont signalés `UNVERIFIED` et ne sont **pas supprimés**. Cette livraison ne prouve donc pas que les huit processus observés ont été nettoyés : elle doit permettre d'isoler précisément ceux qui ne le sont pas.

PROD RUNNING et maintenance ON sont préservés. Aucun appel Symfony depuis le watchdog Caddy. Aucun service ou tâche planifiée modifié par l'installation. Les états persistants et les logs existants ne sont jamais purgés.

## Preuves attendues MAIN

1. `php -l` des PHP modifiés ; `php tests/Unit/FastCgiProcessClassification067Test.php` ; lint Twig ; `git diff --check`.
2. `php bin/console ezs:services diagnostics` : catégories de chaque PID.
3. `php bin/console ezs:services tick` : timings et non-régression.
4. Navigateur Infrastructure : mesure PROD, rafraîchissement, dernier état connu en cas d'échec AJAX ; maintien de la page maintenance publique 503.

Rollback via `install.ps1 -Rollback`, sauvegarde sous `H:/temp/EZS_FASTCGI_OBSERVABILITY_R1/backup`.
