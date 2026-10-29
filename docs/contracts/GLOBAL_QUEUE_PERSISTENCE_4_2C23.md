# Queue globale persistante — tranche 4.2c23

Une seule queue Orchestrator, agnostique du métier et de la provenance (LAB, Assistant ; EZScore plus tard). Nouveau noyau `GlobalQueueStore` SQLite WAL, indépendant du `JobRegistry` historique. La base est **fournie explicitement par l'appelant**, aucune base ni job existant n'est migré automatiquement.

Enveloppe technique immuable : producer, external_id, idempotency_key, kind opaque, resource_class (cpu/gpu), priority. La clé d'idempotence est globale ; (producer,external_id) également unique. Admission et claim utilisent `BEGIN IMMEDIATE` ; attribution par priorité descendante puis FIFO, par classe de ressource. Le token de lease est aléatoire, la génération de claim incrémentée. Finish n'est autorisé que pour le porteur du lease valide. Aucun contenu métier n'est persisté ici.

**Gate de sécurité :** ne pas récupérer les leases expirés, ne pas exposer d'API d'admission ni démarrer de worker sans contrats d'ownership, heartbeat/fencing et retry ; une expiration ne peut pas valider un résultat. Cette tranche n'est pas une migration de flux terminée. Le noyau ne réclame aucun job LAB/Assistant réel, y compris #193, #181/#182/#185. Tests synthétiques en base temporaire uniquement.

Limites : pas encore d'attempts persistées dans ce nouveau noyau, pas de requeue contrôlée, ni dead-letter, ni preuve de concurrence multi-processus. Le contrat d'observabilité 4.2c22 demeure indépendant.
