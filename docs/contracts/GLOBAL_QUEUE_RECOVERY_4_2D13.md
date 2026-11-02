# 4.2d13 — Réconciliation des leases expirés (préparation contrôlée)

`expiredLeases()` inventorie les leases expirés en lecture seule et ne retourne aucun `lease_token`.

`recoverExpired(jobId, claimGeneration, attestStopped)` autorise la remise en queue uniquement si une **autorité indépendante** certifie que l'exécution ancienne est effectivement arrêtée ou neutralisée. L'attestation est effectuée hors transaction pour ne pas monopoliser SQLite, puis une transaction `BEGIN IMMEDIATE` recontrôle état, génération, jeton et expiration. Le changement incrémente `claim_generation`, efface le jeton, conserve le job et enregistre un événement warning. L'ancien token ne peut plus faire de heartbeat ni de finish. Un GPU bloqué ne redevient disponible qu'après cette attestation.

**Limite bloquante :** ce lot n'apporte pas d'implémentation d'attestation réelle des processus MAIN/XPS, ni de planificateur, ni de retry budget; le callback doit provenir du composant de supervision de confiance (pas du producteur). Ne pas brancher un callback retournant toujours true. L'inventaire et la réconciliation ne tournent pas automatiquement après installation. Aucun worker ni transport Messenger activé et aucune donnée MAIN modifiée par les tests.

Vérifications MAIN : php -l, composer validate, lint:container, test ciblé GlobalQueueRecoveryTest, suite PHPUnit complète, UTF-8 sans BOM et git diff --check. Le test SQLite est synthétique et ne démontre pas le fencing d'un processus réel.
