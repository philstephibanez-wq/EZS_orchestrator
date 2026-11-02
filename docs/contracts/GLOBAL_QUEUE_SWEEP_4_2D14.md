# 4.2d14 — Balayage borné des leases expirés

`ExpiredLeaseSweep::run(Closure $attestStopped, int $limit = 25)` inventorie jusqu'à 100 leases expirés et demande au noyau transactionnel de les récupérer **uniquement après une attestation indépendante liée au job et à sa génération**. Un refus d'attestation préserve le job `running` et l'exclusivité GPU. Les échecs inattendus sont propagés, jamais masqués.

Le bilan indique inspected, recovered, blocked et stale. La clé `errors` est réservée (toujours zéro dans cette version). Aucun secret de lease n'est exposé au superviseur via l'inventaire.

**Ne pas enregistrer cette classe comme service Symfony autowiré automatiquement avant l'injection d'une configuration canonique pour GlobalQueueStore.** Aucun contrôleur, cron, tâche Windows, worker, route REST ni transport Messenger n'est ajouté. En particulier, le callback d'attestation ne doit jamais retourner true sans preuve d'arrêt/fencing de l'exécuteur. Le raccordement de l'autorité MAIN/XPS et la planification automatique sont différés. Aucun job réel ne doit être récupéré lors de la recette.

Tests sur SQLite synthétique, sous H:\\temp sur MAIN ; recette : `php -l`, `composer validate`, `lint:container`, PHPUnit ciblé et complet, statut Git, UTF-8 sans BOM, `git diff --check`.
