# v2.a52 — correctif contrat bootstrap gateway PHP PROD

La recette MAIN v2.a51 a détecté `GATEWAY_START_MISSING:Gateway` ; le test recherchait `Gateway` avec une majuscule, alors que le paramètre réel dans `scripts/start.ps1` est `gateway` en minuscules. Ce défaut du test n'indique pas un défaut de démarrage, puisqu'aucun démarrage n'a été tenté.

Correction strictement ciblée du test. Validation MAIN déjà constatée : `H:\Caddy\caddy.exe validate --config ...Caddyfile.gateway-php-prod --adapter caddyfile` → `Valid configuration` avec avertissement de formatage non bloquant. Les tests PHP et la mise en service réelle restent à effectuer.

Aucun changement au lanceur, processus ou port, ni à la configuration de PROD. Conserver le processus PHP-CGI 8512 et les Caddy existants. Après test OK, le lancement explicite du gateway `start.ps1 -Target gateway` est l'étape suivante, 8510 étant libre d'après le dernier diagnostic uniquement ; vérifier de nouveau son occupation avant de lancer.

Version 2.a52 ; suivi issue #18.
