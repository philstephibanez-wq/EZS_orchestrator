# 4.2d17 — Frontière de récupération liée à l'identité durable

`TrustedLeaseRecovery` compose **uniquement** les composants canoniques déjà existants : `ExpiredLeaseSweep`, `ExecutorOwnershipRegistry`, `ExecutorStopAttestor` et `GlobalQueueStore`. Pour chaque lease expiré, l'absence d'identité enregistrée par le claim actif interdit la reprise. Une observation indépendante doit fournir `stopped_confirmed` et correspondre à `node`, `pid`, `created_at`, `instance_id`; une identité discordante interdit la reprise. Le store recontrôle état, token, génération et expiration sous `BEGIN IMMEDIATE`, puis invalide l'ancien token.

## Limites bloquantes

Aucune source réelle d'observation MAIN/XPS n'est fournie. Le code accepte une Closure de son appelant : **seul un composant de supervision de confiance peut fournir cette Closure**; le fait de pouvoir en fournir une ne constitue pas une garantie cryptographique contre un appelant malveillant. Ne jamais utiliser de sonde simulée en production. Les données historiques sans identité demeurent bloquées. La disparition d'un PID ne prouve pas toujours l'arrêt de ses processus enfants ou opérations GPU; le superviseur doit attester l'absence du groupe d'exécution et le fencing matériel avant toute libération de slot GPU.

Aucune migration destructive, aucun consommateur Messenger, aucune tâche planifiée, aucun lancement ou arrêt de processus, ni modification PROD. La classe est exclue de l'autowiring; aucune récupération n'est appelée à l'installation. Les tests utilisent exclusivement une SQLite synthétique isolée et une sonde simulée. Pas de récupération automatique opérationnelle validée. Le prochain lot doit introduire l'instrumentation effective du lanceur et la sonde de supervision attestant des groupes de processus.
