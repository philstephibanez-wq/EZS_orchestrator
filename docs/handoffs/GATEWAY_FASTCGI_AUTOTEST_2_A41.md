# v2.a41 — recette Caddy/PHP-FastCGI sur ports isolés

La commande unique `php bin/gateway_fastcgi_autotest.php` lance un backend PHP simulé sur 18511, FastCGI sur 18515 et Caddy candidate sur 18514 ; elle contrôle la conservation de l'URI (y compris query string), les en-têtes X-Forwarded-Proto et le mode maintenance. Elle arrête uniquement les processus créés par la commande, même en cas d'échec. Ports occupés : refus sans action destructive.

Le transport de l'URI originale passe par l'en-tête FastCGI `X-EZS-Original-URI` généré depuis `{http.request.orig_uri}` avant le routage. Cette implémentation reste **candidate** : la recette MAIN doit confirmer la disponibilité du placeholder et la compatibilité Caddy.

Recette : `php tests/GatewayFastcgiAutotestContractTest.php` puis `php bin/gateway_fastcgi_autotest.php`.

Aucun changement aux services PROD 8501, 8510, 8511, 8512. La passerelle Python reste active. Ce test ne constitue pas une validation SSO Google ou médias réelle.
