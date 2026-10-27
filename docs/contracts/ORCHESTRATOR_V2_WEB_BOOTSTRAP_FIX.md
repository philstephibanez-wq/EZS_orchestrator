# V2 Symfony — bootstrap console (1.3b3)

Correction de l'oubli de `web/bin/console` dans la livraison précédente. La console Symfony sert uniquement aux vérifications et opérations de framework, **pas** de nouveau pilote de services. `web/vendor/` et `web/var/` sont locaux et ignorés ; `web/composer.lock` doit être conservé, audité et commité pour des installations reproductibles (généré sur MAIN mais non présent sur GitHub à ce stade). La clé `APP_SECRET` doit être définie localement via environnement ou configuration privée ; ne jamais publier de secret.

Validation utilisateur préalable : `composer validate` OK avec avertissement de licence, `composer install` 37 paquets, échec `bin/console` car absent. Après ce correctif : `php -l bin/console`, `php bin/console about`, `php bin/console debug:router`. Aucune affirmation de succès de ces commandes avant exécution MAIN. Aucun service Caddy, PHP HTTP, rapport ni worker lancé.
