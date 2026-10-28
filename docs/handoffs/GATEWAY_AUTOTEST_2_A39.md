v2.a39 — recette gateway autonome

Commande unique : `php bin/gateway_autotest.php`.

Le script vérifie que les ports 18510/18511/18513 sont libres, lance trois processus de recette via `proc_open` sans shell Windows, attend la disponibilité, invoque la comparaison Python/PHP 10 scénarios et ferme les seuls processus qu’il a créés dans un bloc `finally`, même en cas d’échec. Si un port est occupé il refuse de démarrer et ne touche pas au processus préexistant. Les logs sont hors dépôt sous TEMP/ezs-gateway-recipe-v2a36. Ne touche pas aux ports 8501/8510/8511/8512 ni à leur configuration.

Cette recette ne remplace pas la validation SSO et médias de production. Le serveur HTTP PHP intégré reste réservé aux tests.
