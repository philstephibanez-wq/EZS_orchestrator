# Orchestrator V2 — correctif dépendance Console 1.3b4

Sur MAIN, `composer install` avec la configuration 1.3b3 installait les bundles Symfony mais **pas** `symfony/console`. `php bin/console about` et `debug:router` échouaient sur `Symfony\\Component\\Console\\Application` introuvable. La cause est l'absence de dépendance directe dans `web/composer.json`.

Correction ciblée : ajouter `symfony/console: 7.4.*`. Ne pas introduire de nouvelle CLI métier, ni de serveur PHP/Caddy, ni de tâches Windows. `web/composer.lock` existe localement sur MAIN et doit être mis à jour par Composer, puis versionné après contrôle. `web/vendor/` doit rester ignoré.

Validation existante : l'owner a confirmé `composer validate` OK, `php -l bin/console` OK, échec des commandes console pour dépendance manquante. Tests après correction non exécutés sur MAIN à la publication.
