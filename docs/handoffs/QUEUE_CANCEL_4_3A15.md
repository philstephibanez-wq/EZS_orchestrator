# Queue cancellation 4.3a15 — Orchestrator

- Autorité unique : `global_queue_jobs`; `POST /api/v2/queue/jobs/{id}/cancel` exclusivement pour le producteur authentifié et le peer loopback.
- Transition atomique admise : `queued -> cancelled`; idempotence de la répétition, refus de l'annulation par un autre producteur.
- `running -> cancelled` interdit sans attestation indépendante de l'arrêt de l'exécuteur et de ses enfants : `active_executor_stop_attestation_required`. Un bail expiré ne suffit pas.
- `failed` et `completed` restent des événements historiques terminaux distincts de l'annulation.
- La contrainte de la table SQLite historique requiert la migration contrôlée du schéma, avec sauvegarde avant mutation, index et clés étrangères préservés ; tout `running` bloque l'opération.
- Le tableau de bord affiche désormais l'état Annulé. Les détails scientifiques restent dans LAB.
- Migration effectuée exclusivement par le ZIP de maintenance validé (INSTALL.py) sur MAIN. **Ne pas** rejouer la migration sur une base déjà migrée.
- Non couvert : arrêt d'un job running, admission des jobs LAB antérieurs, démarrage automatique des exécutants et cycle FIFO complet.
