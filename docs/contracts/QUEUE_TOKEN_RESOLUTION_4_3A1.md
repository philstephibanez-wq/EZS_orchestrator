# Orchestrator 4.3a1 — résolution du jeton d'admission REST

Le contrôle Bearer existant conserve ses règles : loopback, jeton de longueur 32–256, correspondance constante, rejet d'une identité ambiguë, validation de l'enveloppe avant toute écriture.

Une variable déclarée dans le `.env.local` Symfony est généralement chargée dans `$_SERVER` et `$_ENV`, sans obligation d'appeler `putenv()`. La résolution du jeton reconnaît donc la variable native `getenv()`, puis `$_SERVER`, puis `$_ENV`. Les injections de tests explicites demeurent prioritaires dans `producerFor()` et n'ont pas changé.

Ce lot n'ajoute aucune route, n'écrit aucun jeton dans Git ou logs et ne modifie ni les services Windows, ni Caddy, ni les jobs. Le provisioning local du secret hors Git et la validation HTTP 422 sont des opérations distinctes ; aucun job global ne peut être admis par ces tests unitaires. Aucun redémarrage de service ni modification de la configuration PROD n'est autorisé par l'installation.
